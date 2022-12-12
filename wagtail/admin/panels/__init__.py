import functools
from warnings import warn

from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
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
from wagtail.admin.widgets.datetime import AdminDateTimeInput
from wagtail.models import COMMENTS_RELATION_NAME, Page
from wagtail.utils.decorators import cached_classmethod
from wagtail.utils.deprecation import RemovedInWagtail50Warning

from .base import *  # NOQA
from .base import Panel
from .field_panel import *  # NOQA
from .field_panel import FieldPanel
from .group import *  # NOQA
from .group import (
    FieldRowPanel,
    MultiFieldPanel,
    ObjectList,
    PanelGroup,
    TabbedInterface,
)
from .help_panel import *  # NOQA
from .page_chooser_panel import *  # NOQA


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


class BaseCompositeEditHandler(PanelGroup):
    def __init__(self, *args, **kwargs):
        warn(
            "wagtail.admin.edit_handlers.BaseCompositeEditHandler has been renamed to wagtail.admin.panels.PanelGroup",
            category=RemovedInWagtail50Warning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


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
