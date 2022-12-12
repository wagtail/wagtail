import functools
from warnings import warn

from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.core.signals import setting_changed
from django.dispatch import receiver
from django.forms import Media
from django.forms.formsets import DELETION_FIELD_NAME, ORDERING_FIELD_NAME
from django.forms.models import fields_for_model
from django.utils.functional import cached_property
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy
from modelcluster.models import get_serializable_data_for_fields

from wagtail.admin import compare
from wagtail.admin.forms.comments import CommentForm

# DIRECT_FORM_FIELD_OVERRIDES, FORM_FIELD_OVERRIDES are imported for backwards
# compatibility, as people are likely importing them from here and then
# appending their own overrides
from wagtail.admin.forms.models import (  # NOQA
    DIRECT_FORM_FIELD_OVERRIDES,
    FORM_FIELD_OVERRIDES,
    formfield_for_dbfield,
)
from wagtail.admin.forms.pages import WagtailAdminPageForm
from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.templatetags.wagtailadmin_tags import avatar_url, user_display_name
from wagtail.admin.widgets import AdminPageChooser
from wagtail.admin.widgets.datetime import AdminDateTimeInput
from wagtail.blocks import BlockField
from wagtail.models import COMMENTS_RELATION_NAME, Page
from wagtail.utils.decorators import cached_classmethod
from wagtail.utils.deprecation import RemovedInWagtail50Warning

from .base import *  # NOQA
from .base import Panel


def extract_panel_definitions_from_model_class(model, exclude=None):
    if hasattr(model, "panels"):
        return model.panels

    panels = []

    _exclude = []
    if exclude:
        _exclude.extend(exclude)

    fields = fields_for_model(
        model, exclude=_exclude, formfield_callback=formfield_for_dbfield
    )

    for field_name, field in fields.items():
        try:
            panel_class = field.widget.get_panel()
        except AttributeError:
            panel_class = FieldPanel

        panel = panel_class(field_name)
        panels.append(panel)

    return panels


class EditHandler(Panel):
    def __init__(self, *args, **kwargs):
        warn(
            "wagtail.admin.edit_handlers.EditHandler has been renamed to wagtail.admin.panels.Panel",
            category=RemovedInWagtail50Warning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


class PanelGroup(Panel):
    """
    Abstract class for panels that manage a set of sub-panels.
    Concrete subclasses must attach a 'children' property
    """

    def __init__(self, children=(), *args, **kwargs):
        permission = kwargs.pop("permission", None)
        super().__init__(*args, **kwargs)
        self.children = children
        self.permission = permission

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        kwargs["children"] = self.children
        kwargs["permission"] = self.permission
        return kwargs

    def get_form_options(self):
        if self.model is None:
            raise AttributeError(
                "%s is not bound to a model yet. Use `.bind_to_model(model)` "
                "before using this method." % self.__class__.__name__
            )

        options = {}

        # Merge in form options from each child in turn, combining values that are types that we
        # know how to combine (i.e. lists, dicts and sets)
        for child in self.children:
            child_options = child.get_form_options()
            for key, new_val in child_options.items():
                if key not in options:
                    # if val is a known mutable container type that we're going to merge subsequent
                    # child values into, create a copy so that we don't risk that change leaking
                    # back into the child's internal state
                    if (
                        isinstance(new_val, list)
                        or isinstance(new_val, dict)
                        or isinstance(new_val, set)
                    ):
                        options[key] = new_val.copy()
                    else:
                        options[key] = new_val
                else:
                    current_val = options[key]
                    if isinstance(current_val, list) and isinstance(
                        new_val, (list, tuple)
                    ):
                        current_val.extend(new_val)
                    elif isinstance(current_val, tuple) and isinstance(
                        new_val, (list, tuple)
                    ):
                        options[key] = list(current_val).extend(new_val)
                    elif isinstance(current_val, dict) and isinstance(new_val, dict):
                        current_val.update(new_val)
                    elif isinstance(current_val, set) and isinstance(new_val, set):
                        current_val.update(new_val)
                    else:
                        raise ValueError(
                            "Don't know how to merge values %r and %r for form option %r"
                            % (current_val, new_val, key)
                        )

        return options

    def on_model_bound(self):
        self.children = [child.bind_to_model(self.model) for child in self.children]

    @cached_property
    def child_identifiers(self):
        """
        A list of identifiers corresponding to child panels in ``self.children``, formed from the clean_name property
        but validated to be unique and non-empty.
        """
        used_names = set()
        result = []
        for panel in self.children:
            base_name = panel.clean_name or "panel"
            candidate_name = base_name
            suffix = 0
            while candidate_name in used_names:
                suffix += 1
                candidate_name = "%s%d" % (base_name, suffix)

            result.append(candidate_name)
            used_names.add(candidate_name)

        return result

    class BoundPanel(Panel.BoundPanel):
        @cached_property
        def children(self):
            return [
                child.get_bound_panel(
                    instance=self.instance,
                    request=self.request,
                    form=self.form,
                    prefix=("%s-child-%s" % (self.prefix, identifier)),
                )
                for child, identifier in zip(
                    self.panel.children, self.panel.child_identifiers
                )
            ]

        @cached_property
        def visible_children(self):
            return [child for child in self.children if child.is_shown()]

        @cached_property
        def visible_children_with_identifiers(self):
            return [
                (child, identifier)
                for child, identifier in zip(
                    self.children, self.panel.child_identifiers
                )
                if child.is_shown()
            ]

        def show_panel_furniture(self):
            return any(child.show_panel_furniture() for child in self.children)

        def is_shown(self):
            """
            Check permissions on the panel group overall then check if any children
            are shown.
            """

            if self.panel.permission:
                if not self.request.user.has_perm(self.panel.permission):
                    return False

            return any(child.is_shown() for child in self.children)

        @property
        def media(self):
            media = Media()
            for item in self.visible_children:
                media += item.media
            return media

        def get_comparison(self):
            comparators = []

            for child in self.children:
                comparators.extend(child.get_comparison())

            return comparators


class BaseCompositeEditHandler(PanelGroup):
    def __init__(self, *args, **kwargs):
        warn(
            "wagtail.admin.edit_handlers.BaseCompositeEditHandler has been renamed to wagtail.admin.panels.PanelGroup",
            category=RemovedInWagtail50Warning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


class TabbedInterface(PanelGroup):
    class BoundPanel(PanelGroup.BoundPanel):
        template_name = "wagtailadmin/panels/tabbed_interface.html"


class ObjectList(PanelGroup):
    class BoundPanel(PanelGroup.BoundPanel):
        template_name = "wagtailadmin/panels/object_list.html"


class FieldRowPanel(PanelGroup):
    class BoundPanel(PanelGroup.BoundPanel):
        template_name = "wagtailadmin/panels/field_row_panel.html"


class MultiFieldPanel(PanelGroup):
    class BoundPanel(PanelGroup.BoundPanel):
        template_name = "wagtailadmin/panels/multi_field_panel.html"


class HelpPanel(Panel):
    def __init__(
        self,
        content="",
        template="wagtailadmin/panels/help_panel.html",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.content = content
        self.template = template

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        del kwargs["help_text"]
        kwargs.update(
            content=self.content,
            template=self.template,
        )
        return kwargs

    @property
    def clean_name(self):
        return super().clean_name or "help"

    class BoundPanel(Panel.BoundPanel):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.template_name = self.panel.template
            self.content = self.panel.content


class FieldPanel(Panel):
    TEMPLATE_VAR = "field_panel"

    def __init__(
        self, field_name, widget=None, disable_comments=None, permission=None, **kwargs
    ):
        super().__init__(**kwargs)
        self.field_name = field_name
        self.widget = widget
        self.disable_comments = disable_comments
        self.permission = permission

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        kwargs.update(
            field_name=self.field_name,
            widget=self.widget,
            disable_comments=self.disable_comments,
            permission=self.permission,
        )
        return kwargs

    def get_form_options(self):
        opts = {
            "fields": [self.field_name],
        }
        if self.widget:
            opts["widgets"] = {self.field_name: self.widget}

        if self.permission:
            opts["field_permissions"] = {self.field_name: self.permission}

        return opts

    def get_comparison_class(self):
        try:
            field = self.db_field

            if field.choices:
                return compare.ChoiceFieldComparison

            comparison_class = compare.comparison_class_registry.get(field)
            if comparison_class:
                return comparison_class

            if field.is_relation:
                if field.many_to_many:
                    return compare.M2MFieldComparison

                return compare.ForeignObjectComparison

        except FieldDoesNotExist:
            pass

        return compare.FieldComparison

    @cached_property
    def db_field(self):
        try:
            model = self.model
        except AttributeError:
            raise ImproperlyConfigured(
                "%r must be bound to a model before calling db_field" % self
            )

        return model._meta.get_field(self.field_name)

    @property
    def clean_name(self):
        return self.field_name

    def __repr__(self):
        return "<%s '%s' with model=%s>" % (
            self.__class__.__name__,
            self.field_name,
            self.model,
        )

    class BoundPanel(Panel.BoundPanel):
        template_name = "wagtailadmin/panels/field_panel.html"

        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            if self.form is None:
                self.bound_field = None
                return

            try:
                self.bound_field = self.form[self.field_name]
            except KeyError:
                self.bound_field = None
                return

            if self.panel.heading:
                self.heading = self.bound_field.label = self.panel.heading
            else:
                self.heading = self.bound_field.label

            self.help_text = self.panel.help_text or self.bound_field.help_text

        @property
        def field_name(self):
            return self.panel.field_name

        def is_shown(self):
            if self.form is not None and self.bound_field is None:
                # this field is missing from the form
                return False

            if (
                self.panel.permission
                and self.request
                and not self.request.user.has_perm(self.panel.permission)
            ):
                return False

            return True

        def is_required(self):
            return self.bound_field.field.required

        def classes(self):
            is_streamfield = isinstance(self.bound_field.field, BlockField)
            extra_classes = ["w-panel--nested"] if is_streamfield else []

            return self.panel.classes() + extra_classes

        @property
        def icon(self):
            """
            Display a different icon depending on the field’s type.
            """
            field_icons = {
                # Icons previously-defined as StreamField block icons.
                # Commented out until they can be reviewed for appropriateness in this new context.
                # "DateField": "date",
                # "TimeField": "time",
                # "DateTimeField": "date",
                # "URLField": "site",
                # "ClusterTaggableManager": "tag",
                # "EmailField": "mail",
                # "TextField": "pilcrow",
                # "FloatField": "plus-inverse",
                # "DecimalField": "plus-inverse",
                # "RegexField": "code",
                # "BooleanField": "tick-inverse",
            }
            field_type = self.bound_field.field.__class__.__name__

            return self.panel.icon or field_icons.get(field_type, None)

        def id_for_label(self):
            return self.bound_field.id_for_label

        @property
        def comments_enabled(self):
            if self.panel.disable_comments is None:
                # by default, enable comments on all fields except StreamField (which has its own comment handling)
                return not isinstance(self.bound_field.field, BlockField)
            else:
                return not self.panel.disable_comments

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)

            widget_described_by_ids = []
            help_text = self.bound_field.help_text
            help_text_id = "%s-helptext" % self.prefix
            error_message_id = "%s-errors" % self.prefix

            if help_text:
                widget_described_by_ids.append(help_text_id)

            if self.bound_field.errors:
                widget = self.bound_field.field.widget
                if hasattr(widget, "render_with_errors"):
                    widget_attrs = {
                        "id": self.bound_field.auto_id,
                    }
                    if widget_described_by_ids:
                        widget_attrs["aria-describedby"] = " ".join(
                            widget_described_by_ids
                        )

                    rendered_field = widget.render_with_errors(
                        self.bound_field.html_name,
                        self.bound_field.value(),
                        attrs=widget_attrs,
                        errors=self.bound_field.errors,
                    )
                else:
                    widget_described_by_ids.append(error_message_id)
                    rendered_field = self.bound_field.as_widget(
                        attrs={
                            "aria-invalid": "true",
                            "aria-describedby": " ".join(widget_described_by_ids),
                        }
                    )
            else:
                widget_attrs = {}
                if widget_described_by_ids:
                    widget_attrs["aria-describedby"] = " ".join(widget_described_by_ids)

                rendered_field = self.bound_field.as_widget(attrs=widget_attrs)

            context.update(
                {
                    "field": self.bound_field,
                    "rendered_field": rendered_field,
                    "help_text": help_text,
                    "help_text_id": help_text_id,
                    "error_message_id": error_message_id,
                    "show_add_comment_button": self.comments_enabled
                    and getattr(
                        self.bound_field.field.widget, "show_add_comment_button", True
                    ),
                }
            )
            return context

        def get_comparison(self):
            comparator_class = self.panel.get_comparison_class()

            if comparator_class and self.is_shown():
                try:
                    return [functools.partial(comparator_class, self.panel.db_field)]
                except FieldDoesNotExist:
                    return []
            return []

        def __repr__(self):
            return "<%s '%s' with model=%s instance=%s request=%s form=%s>" % (
                self.__class__.__name__,
                self.field_name,
                self.panel.model,
                self.instance,
                self.request,
                self.form.__class__.__name__,
            )


class RichTextFieldPanel(FieldPanel):
    def __init__(self, *args, **kwargs):
        warn(
            "RichTextFieldPanel is no longer required for rich text fields, and should be replaced by FieldPanel. "
            "RichTextFieldPanel will be removed in a future release. "
            "See https://docs.wagtail.org/en/stable/releases/3.0.html#removal-of-special-purpose-field-panel-types",
            category=RemovedInWagtail50Warning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


class BaseChooserPanel(FieldPanel):
    def __init__(self, *args, **kwargs):
        warn(
            "wagtail.admin.edit_handlers.BaseChooserPanel is obsolete and should be replaced by wagtail.admin.panels.FieldPanel",
            category=RemovedInWagtail50Warning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


class PageChooserPanel(FieldPanel):
    def __init__(self, field_name, page_type=None, can_choose_root=False):
        super().__init__(field_name=field_name)

        self.page_type = page_type
        self.can_choose_root = can_choose_root

    def clone_kwargs(self):
        return {
            "field_name": self.field_name,
            "page_type": self.page_type,
            "can_choose_root": self.can_choose_root,
        }

    def get_form_options(self):
        opts = super().get_form_options()

        if self.page_type or self.can_choose_root:
            widgets = opts.setdefault("widgets", {})
            widgets[self.field_name] = AdminPageChooser(
                target_models=self.page_type, can_choose_root=self.can_choose_root
            )

        return opts


class InlinePanel(Panel):
    def __init__(
        self,
        relation_name,
        panels=None,
        heading="",
        label="",
        min_num=None,
        max_num=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.relation_name = relation_name
        self.panels = panels
        self.heading = heading or label
        self.label = label
        self.min_num = min_num
        self.max_num = max_num

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        kwargs.update(
            relation_name=self.relation_name,
            panels=self.panels,
            label=self.label,
            min_num=self.min_num,
            max_num=self.max_num,
        )
        return kwargs

    @cached_property
    def panel_definitions(self):
        # Look for a panels definition in the InlinePanel declaration
        if self.panels is not None:
            return self.panels
        # Failing that, get it from the model
        return extract_panel_definitions_from_model_class(
            self.db_field.related_model, exclude=[self.db_field.field.name]
        )

    @cached_property
    def child_edit_handler(self):
        panels = self.panel_definitions
        child_edit_handler = MultiFieldPanel(panels, heading=self.heading)
        return child_edit_handler.bind_to_model(self.db_field.related_model)

    def get_form_options(self):
        child_form_opts = self.child_edit_handler.get_form_options()
        return {
            "formsets": {
                self.relation_name: {
                    "fields": child_form_opts.get("fields", []),
                    "widgets": child_form_opts.get("widgets", {}),
                    "min_num": self.min_num,
                    "validate_min": self.min_num is not None,
                    "max_num": self.max_num,
                    "validate_max": self.max_num is not None,
                    "formsets": child_form_opts.get("formsets"),
                }
            }
        }

    def on_model_bound(self):
        manager = getattr(self.model, self.relation_name)
        self.db_field = manager.rel

    def classes(self):
        return super().classes() + ["w-panel--nested"]

    class BoundPanel(Panel.BoundPanel):
        template_name = "wagtailadmin/panels/inline_panel.html"

        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            self.label = self.panel.label

            if self.form is None:
                return

            self.formset = self.form.formsets[self.panel.relation_name]
            self.child_edit_handler = self.panel.child_edit_handler

            self.children = []
            for index, subform in enumerate(self.formset.forms):
                # override the DELETE field to have a hidden input
                subform.fields[DELETION_FIELD_NAME].widget = forms.HiddenInput()

                # ditto for the ORDER field, if present
                if self.formset.can_order:
                    subform.fields[ORDERING_FIELD_NAME].widget = forms.HiddenInput()

                self.children.append(
                    self.child_edit_handler.get_bound_panel(
                        instance=subform.instance,
                        request=self.request,
                        form=subform,
                        prefix=("%s-%d" % (self.prefix, index)),
                    )
                )

            # if this formset is valid, it may have been re-ordered; respect that
            # in case the parent form errored and we need to re-render
            if self.formset.can_order and self.formset.is_valid():
                self.children.sort(
                    key=lambda child: child.form.cleaned_data[ORDERING_FIELD_NAME] or 1
                )

            empty_form = self.formset.empty_form
            empty_form.fields[DELETION_FIELD_NAME].widget = forms.HiddenInput()
            if self.formset.can_order:
                empty_form.fields[ORDERING_FIELD_NAME].widget = forms.HiddenInput()

            self.empty_child = self.child_edit_handler.get_bound_panel(
                instance=empty_form.instance,
                request=self.request,
                form=empty_form,
                prefix=("%s-__prefix__" % self.prefix),
            )

        def get_comparison(self):
            field_comparisons = []

            for index, panel in enumerate(self.panel.child_edit_handler.children):
                field_comparisons.extend(
                    panel.get_bound_panel(
                        instance=None,
                        request=self.request,
                        form=None,
                        prefix=("%s-%d" % (self.prefix, index)),
                    ).get_comparison()
                )

            return [
                functools.partial(
                    compare.ChildRelationComparison,
                    self.panel.db_field,
                    field_comparisons,
                    label=self.label,
                )
            ]

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            context["can_order"] = self.formset.can_order
            return context


# This allows users to include the publishing panel in their own per-model override
# without having to write these fields out by hand, potentially losing 'classname'
# and therefore the associated styling of the publishing panel
class PublishingPanel(MultiFieldPanel):
    def __init__(self, **kwargs):
        js_overlay_parent_selector = "#schedule-publishing-dialog"
        updated_kwargs = {
            "children": [
                FieldRowPanel(
                    [
                        FieldPanel(
                            "go_live_at",
                            widget=AdminDateTimeInput(
                                js_overlay_parent_selector=js_overlay_parent_selector,
                            ),
                        ),
                        FieldPanel(
                            "expire_at",
                            widget=AdminDateTimeInput(
                                js_overlay_parent_selector=js_overlay_parent_selector,
                            ),
                        ),
                    ],
                ),
            ],
            "classname": "publishing",
        }
        updated_kwargs.update(kwargs)
        super().__init__(**updated_kwargs)

    @property
    def clean_name(self):
        return super().clean_name or "publishing"

    class BoundPanel(PanelGroup.BoundPanel):
        template_name = "wagtailadmin/panels/publishing/schedule_publishing_panel.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            context["request"] = self.request
            context["instance"] = self.instance
            context["classname"] = self.classname
            if isinstance(self.instance, Page):
                context["page"] = self.instance
            return context

        def show_panel_furniture(self):
            return False

        @property
        def media(self):
            return super().media + Media(
                js=[versioned_static("wagtailadmin/js/schedule-publishing.js")],
            )


class CommentPanel(Panel):
    def get_form_options(self):
        # add the comments formset
        return {
            # Adds the comment notifications field to the form.
            # Note, this field is defined directly on WagtailAdminPageForm.
            "fields": ["comment_notifications"],
            "formsets": {
                COMMENTS_RELATION_NAME: {
                    "form": CommentForm,
                    "fields": ["text", "contentpath", "position"],
                    "formset_name": "comments",
                    "inherit_kwargs": ["for_user"],
                }
            },
        }

    @property
    def clean_name(self):
        return super().clean_name or "commments"

    class BoundPanel(Panel.BoundPanel):
        template_name = "wagtailadmin/panels/comments/comment_panel.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)

            def user_data(user):
                return {"name": user_display_name(user), "avatar_url": avatar_url(user)}

            user = getattr(self.request, "user", None)
            user_pks = {user.pk}
            serialized_comments = []
            bound = self.form.is_bound
            comment_formset = self.form.formsets.get("comments")
            comment_forms = comment_formset.forms if comment_formset else []
            for form in comment_forms:
                # iterate over comments to retrieve users (to get display names) and serialized versions
                replies = []
                for reply_form in form.formsets["replies"].forms:
                    user_pks.add(reply_form.instance.user_id)
                    reply_data = get_serializable_data_for_fields(reply_form.instance)
                    reply_data["deleted"] = (
                        reply_form.cleaned_data.get("DELETE", False) if bound else False
                    )
                    replies.append(reply_data)
                user_pks.add(form.instance.user_id)
                data = get_serializable_data_for_fields(form.instance)
                data["deleted"] = (
                    form.cleaned_data.get("DELETE", False) if bound else False
                )
                data["resolved"] = (
                    form.cleaned_data.get("resolved", False)
                    if bound
                    else form.instance.resolved_at is not None
                )
                data["replies"] = replies
                serialized_comments.append(data)

            authors = {
                str(user.pk): user_data(user)
                for user in get_user_model()
                .objects.filter(pk__in=user_pks)
                .select_related("wagtail_userprofile")
            }

            comments_data = {
                "comments": serialized_comments,
                "user": user.pk,
                "authors": authors,
            }

            context["comments_data"] = comments_data
            return context

        def show_panel_furniture(self):
            return False


# Now that we've defined panels, we can set up wagtailcore.Page to have some.
def set_default_page_edit_handlers(cls):
    cls.content_panels = [
        FieldPanel(
            "title",
            classname="title",
            widget=forms.TextInput(
                attrs={
                    "placeholder": format_lazy(
                        "{title}*", title=gettext_lazy("Page title")
                    )
                }
            ),
        ),
    ]

    cls.promote_panels = [
        MultiFieldPanel(
            [
                FieldPanel("slug"),
                FieldPanel("seo_title"),
                FieldPanel("search_description"),
            ],
            gettext_lazy("For search engines"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("show_in_menus"),
            ],
            gettext_lazy("For site menus"),
        ),
    ]

    cls.settings_panels = [
        PublishingPanel(),
    ]

    if getattr(settings, "WAGTAILADMIN_COMMENTS_ENABLED", True):
        cls.settings_panels.append(CommentPanel())

    cls.base_form_class = WagtailAdminPageForm


set_default_page_edit_handlers(Page)


@cached_classmethod
def _get_page_edit_handler(cls):
    """
    Get the panel to use in the Wagtail admin when editing this page type.
    """
    if hasattr(cls, "edit_handler"):
        edit_handler = cls.edit_handler
    else:
        # construct a TabbedInterface made up of content_panels, promote_panels
        # and settings_panels, skipping any which are empty
        tabs = []

        if cls.content_panels:
            tabs.append(ObjectList(cls.content_panels, heading=gettext_lazy("Content")))
        if cls.promote_panels:
            tabs.append(ObjectList(cls.promote_panels, heading=gettext_lazy("Promote")))
        if cls.settings_panels:
            tabs.append(
                ObjectList(cls.settings_panels, heading=gettext_lazy("Settings"))
            )

        edit_handler = TabbedInterface(tabs, base_form_class=cls.base_form_class)

    return edit_handler.bind_to_model(cls)


Page.get_edit_handler = _get_page_edit_handler


@functools.lru_cache(maxsize=None)
def get_edit_handler(model):
    """
    Get the panel to use in the Wagtail admin when editing this model.
    """
    if hasattr(model, "edit_handler"):
        # use the edit handler specified on the model class
        panel = model.edit_handler
    else:
        panels = extract_panel_definitions_from_model_class(model)
        panel = ObjectList(panels)

    return panel.bind_to_model(model)


@receiver(setting_changed)
def reset_edit_handler_cache(**kwargs):
    """
    Clear page edit handler cache when global WAGTAILADMIN_COMMENTS_ENABLED settings are changed
    """
    if kwargs["setting"] == "WAGTAILADMIN_COMMENTS_ENABLED":
        set_default_page_edit_handlers(Page)
        for model in apps.get_models():
            if issubclass(model, Page):
                model.get_edit_handler.cache_clear()
        get_edit_handler.cache_clear()


class StreamFieldPanel(FieldPanel):
    def __init__(self, *args, **kwargs):
        warn(
            "StreamFieldPanel is no longer required when using StreamField, and should be replaced by FieldPanel. "
            "StreamFieldPanel will be removed in a future release. "
            "See https://docs.wagtail.org/en/stable/releases/3.0.html#removal-of-special-purpose-field-panel-types",
            category=RemovedInWagtail50Warning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
