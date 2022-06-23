import functools
import re
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
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy
from modelcluster.models import get_serializable_data_for_fields

from wagtail.admin import compare
from wagtail.admin.forms.comments import CommentForm
from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.templatetags.wagtailadmin_tags import avatar_url, user_display_name
from wagtail.admin.ui.components import Component
from wagtail.admin.widgets import AdminPageChooser
from wagtail.blocks import BlockField
from wagtail.coreutils import camelcase_to_underscore
from wagtail.models import COMMENTS_RELATION_NAME, Page
from wagtail.utils.decorators import cached_classmethod
from wagtail.utils.deprecation import RemovedInWagtail50Warning

# DIRECT_FORM_FIELD_OVERRIDES, FORM_FIELD_OVERRIDES are imported for backwards
# compatibility, as people are likely importing them from here and then
# appending their own overrides
from .forms.models import (  # NOQA
    DIRECT_FORM_FIELD_OVERRIDES,
    FORM_FIELD_OVERRIDES,
    WagtailAdminModelForm,
    formfield_for_dbfield,
)
from .forms.pages import WagtailAdminPageForm


def get_form_for_model(
    model,
    form_class=WagtailAdminModelForm,
    **kwargs,
):
    """
    Construct a ModelForm subclass using the given model and base form class. Any additional
    keyword arguments are used to populate the form's Meta class.
    """

    # This is really just Django's modelform_factory, tweaked to accept arbitrary kwargs.

    meta_class_attrs = kwargs
    meta_class_attrs["model"] = model

    # The kwargs passed here are expected to come from EditHandler.get_form_options, which collects
    # them by descending the tree of child edit handlers. If there are no edit handlers that
    # specify form fields, this can legitimately result in both 'fields' and 'exclude' being
    # absent, which ModelForm doesn't normally allow. In this case, explicitly set fields to [].
    if "fields" not in meta_class_attrs and "exclude" not in meta_class_attrs:
        meta_class_attrs["fields"] = []

    # Give this new form class a reasonable name.
    class_name = model.__name__ + "Form"
    bases = (form_class.Meta,) if hasattr(form_class, "Meta") else ()
    Meta = type("Meta", bases, meta_class_attrs)
    form_class_attrs = {"Meta": Meta}

    metaclass = type(form_class)
    return metaclass(class_name, (form_class,), form_class_attrs)


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


class Panel:
    """
    Defines part (or all) of the edit form interface for pages and other models within the Wagtail
    admin. Each model has an associated panel definition, consisting of a nested structure of Panel
    objects - this provides methods for obtaining a ModelForm subclass, with the field list and
    other parameters collated from all panels in the structure. It then handles rendering that form
    as HTML.
    """

    def __init__(self, heading="", classname="", help_text="", base_form_class=None):
        self.heading = heading
        self.classname = classname
        self.help_text = help_text
        self.base_form_class = base_form_class
        self.model = None

    def clone(self):
        """
        Create a clone of this panel definition. By default, constructs a new instance, passing the
        keyword arguments returned by ``clone_kwargs``.
        """
        return self.__class__(**self.clone_kwargs())

    def clone_kwargs(self):
        """
        Return a dictionary of keyword arguments that can be used to create a clone of this panel definition.
        """
        return {
            "heading": self.heading,
            "classname": self.classname,
            "help_text": self.help_text,
            "base_form_class": self.base_form_class,
        }

    def get_form_options(self):
        """
        Return a dictionary of attributes such as 'fields', 'formsets' and 'widgets'
        which should be incorporated into the form class definition to generate a form
        that this panel can use.
        This will only be called after binding to a model (i.e. self.model is available).
        """
        options = {}

        if not getattr(self.widget_overrides, "is_original_method", False):
            warn(
                "The `widget_overrides` method (on %r) is deprecated; "
                "these should be returned from `get_form_options` as a "
                "`widgets` item instead." % type(self),
                category=RemovedInWagtail50Warning,
            )
            options["widgets"] = self.widget_overrides()

        if not getattr(self.required_fields, "is_original_method", False):
            warn(
                "The `required_fields` method (on %r) is deprecated; "
                "these should be returned from `get_form_options` as a "
                "`fields` item instead." % type(self),
                category=RemovedInWagtail50Warning,
            )
            options["fields"] = self.required_fields()

        if not getattr(self.required_formsets, "is_original_method", False):
            warn(
                "The `required_formsets` method (on %r) is deprecated; "
                "these should be returned from `get_form_options` as a "
                "`formsets` item instead." % type(self),
                category=RemovedInWagtail50Warning,
            )
            options["formsets"] = self.required_formsets()

        return options

    # RemovedInWagtail50Warning - edit handlers should override get_form_options instead
    def widget_overrides(self):
        return {}

    widget_overrides.is_original_method = True

    # RemovedInWagtail50Warning - edit handlers should override get_form_options instead
    def required_fields(self):
        return []

    required_fields.is_original_method = True

    # RemovedInWagtail50Warning - edit handlers should override get_form_options instead
    def required_formsets(self):
        return {}

    required_formsets.is_original_method = True

    def get_form_class(self):
        """
        Construct a form class that has all the fields and formsets named in
        the children of this edit handler.
        """
        form_options = self.get_form_options()
        # If a custom form class was passed to the EditHandler, use it.
        # Otherwise, use the base_form_class from the model.
        # If that is not defined, use WagtailAdminModelForm.
        model_form_class = getattr(self.model, "base_form_class", WagtailAdminModelForm)
        base_form_class = self.base_form_class or model_form_class

        return get_form_for_model(
            self.model,
            form_class=base_form_class,
            **form_options,
        )

    def bind_to_model(self, model):
        """
        Create a clone of this panel definition with a ``model`` attribute pointing to the linked model class.
        """
        new = self.clone()
        new.model = model
        new.on_model_bound()
        return new

    def bind_to(self, model=None, instance=None, request=None, form=None):
        warn(
            "The %s.bind_to() method has been replaced by bind_to_model(model) and get_bound_panel(instance=instance, request=request, form=form)"
            % type(self).__name__,
            category=RemovedInWagtail50Warning,
            stacklevel=2,
        )
        return self.get_bound_panel(instance=instance, request=request, form=form)

    def get_bound_panel(self, instance=None, request=None, form=None):
        """
        Return a ``BoundPanel`` instance that can be rendered onto the template as a component. By default, this creates an instance
        of the panel class's inner ``BoundPanel`` class, which must inherit from ``Panel.BoundPanel``.
        """
        if self.model is None:
            raise ImproperlyConfigured(
                "%s.bind_to_model(model) must be called before get_bound_panel"
                % type(self).__name__
            )

        if not issubclass(self.BoundPanel, EditHandler.BoundPanel):
            raise ImproperlyConfigured(
                "%s.BoundPanel must be a subclass of EditHandler.BoundPanel"
                % type(self).__name__
            )

        return self.BoundPanel(
            panel=self, instance=instance, request=request, form=form
        )

    def on_model_bound(self):
        """
        Called after the panel has been associated with a model class and the ``self.model`` attribute is available;
        panels can override this method to perform additional initialisation related to the model.
        """
        pass

    def __repr__(self):
        return "<%s with model=%s>" % (
            self.__class__.__name__,
            self.model,
        )

    def classes(self):
        """
        Additional CSS classnames to add to whatever kind of object this is at output.
        Subclasses of Panel should override this, invoking super().classes() to
        append more classes specific to the situation.
        """
        if self.classname:
            return [self.classname]
        return []

    def field_type(self):
        """
        The kind of field it is e.g boolean_field. Useful for better semantic markup of field display based on type
        """
        return ""

    def id_for_label(self):
        """
        The ID to be used as the 'for' attribute of any <label> elements that refer
        to this object but are rendered outside of it. Leave blank if this object does not render
        as a single input field.
        """
        return ""

    class BoundPanel(Component):
        """
        A template component for a panel that has been associated with a model instance, form, and request.
        """

        def __init__(self, panel, instance, request, form):
            self.panel = panel
            self.instance = instance
            self.request = request
            self.form = form

            self.heading = self.panel.heading
            self.help_text = self.panel.help_text

        @property
        def classname(self):
            return self.panel.classname

        def classes(self):
            return self.panel.classes()

        def field_type(self):
            return self.panel.field_type()

        def id_for_label(self):
            """
            Returns an HTML ID to be used as the target for any label referencing this panel.
            """
            return self.panel.id_for_label()

        def is_shown(self):
            """
            Whether this panel should be rendered; if false, it is skipped in the template output.
            """
            return True

        def render_as_object(self):
            return self.render_html()

        def render_as_field(self):
            return self.render_html()

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            context["self"] = self
            return context

        def get_comparison(self):
            return []

        def render_missing_fields(self):
            """
            Helper function: render all of the fields that are defined on the form but not "claimed" by
            any panels via required_fields. These fields are most likely to be hidden fields introduced
            by the forms framework itself, such as ORDER / DELETE fields on formset members.
            (If they aren't actually hidden fields, then they will appear as ugly unstyled / label-less fields
            outside of the panel furniture. But there's not much we can do about that.)
            """
            rendered_fields = self.panel.get_form_options().get("fields", [])
            missing_fields_html = [
                str(self.form[field_name])
                for field_name in self.form.fields
                if field_name not in rendered_fields
            ]

            return mark_safe("".join(missing_fields_html))

        def render_form_content(self):
            """
            Render this as an 'object', ensuring that all fields necessary for a valid form
            submission are included
            """
            return mark_safe(self.render_as_object() + self.render_missing_fields())

        def __repr__(self):
            return "<%s with model=%s instance=%s request=%s form=%s>" % (
                self.__class__.__name__,
                self.panel.model,
                self.instance,
                self.request,
                self.form.__class__.__name__,
            )


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
        super().__init__(*args, **kwargs)
        self.children = children

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        kwargs["children"] = self.children
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

    class BoundPanel(Panel.BoundPanel):
        def __init__(self, panel, instance, request, form):
            super().__init__(panel=panel, instance=instance, request=request, form=form)

        @cached_property
        def children(self):
            return [
                child.get_bound_panel(
                    instance=self.instance, request=self.request, form=self.form
                )
                for child in self.panel.children
            ]

        @cached_property
        def visible_children(self):
            return [child for child in self.children if child.is_shown()]

        def is_shown(self):
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

        def visible_children_with_classnames(self):
            visible_children = self.visible_children
            col_count = " col%s" % (12 // len(visible_children))
            for child in visible_children:
                classname = " ".join(child.classes())
                if not re.search(r"\bcol\d+\b", classname):
                    classname += col_count
                yield child, classname


class MultiFieldPanel(PanelGroup):
    def classes(self):
        classes = super().classes()
        classes.append("multi-field")
        return classes

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

    class BoundPanel(Panel.BoundPanel):
        def __init__(self, panel, instance, request, form):
            super().__init__(panel, instance, request, form)
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

    def __repr__(self):
        return "<%s '%s' with model=%s>" % (
            self.__class__.__name__,
            self.field_name,
            self.model,
        )

    class BoundPanel(Panel.BoundPanel):
        object_template_name = "wagtailadmin/panels/single_field_panel.html"
        field_template_name = "wagtailadmin/panels/field_panel_field.html"

        def __init__(self, panel, instance, request, form):
            super().__init__(panel=panel, instance=instance, request=request, form=form)

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

            self.help_text = self.bound_field.help_text

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

        def classes(self):
            classes = self.panel.classes().copy()

            if self.bound_field.field.required:
                classes.append("required")

            # If field has any errors, add the classname 'error' to enable error styling
            # (e.g. red background), unless the widget has its own mechanism for rendering errors
            # via the render_with_errors mechanism (as StreamField does).
            if self.bound_field.errors and not hasattr(
                self.bound_field.field.widget, "render_with_errors"
            ):
                classes.append("error")

            classes.append(self.field_type())

            return classes

        def field_type(self):
            return camelcase_to_underscore(self.bound_field.field.__class__.__name__)

        def id_for_label(self):
            return self.bound_field.id_for_label

        @property
        def comments_enabled(self):
            if self.panel.disable_comments is None:
                # by default, enable comments on all fields except StreamField (which has its own comment handling)
                return not isinstance(self.bound_field.field, BlockField)
            else:
                return not self.panel.disable_comments

        def render_as_object(self):
            return render_to_string(
                self.object_template_name,
                {
                    "self": self,
                    self.panel.TEMPLATE_VAR: self,
                    "field": self.bound_field,
                    "show_add_comment_button": self.comments_enabled
                    and getattr(
                        self.bound_field.field.widget, "show_add_comment_button", True
                    ),
                },
            )

        def render_as_field(self):
            return render_to_string(
                self.field_template_name,
                {
                    "field": self.bound_field,
                    "field_type": self.field_type(),
                    "show_add_comment_button": self.comments_enabled
                    and getattr(
                        self.bound_field.field.widget, "show_add_comment_button", True
                    ),
                },
            )

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
            "wagtail.admin.edit_handlers.RichTextFieldPanel is obsolete and should be replaced by wagtail.admin.panels.FieldPanel",
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

    class BoundPanel(Panel.BoundPanel):
        template_name = "wagtailadmin/panels/inline_panel.html"

        def __init__(self, panel, instance, request, form):
            super().__init__(panel, instance, request, form)

            self.label = self.panel.label

            if self.form is None:
                return

            self.formset = self.form.formsets[self.panel.relation_name]
            self.child_edit_handler = self.panel.child_edit_handler

            self.children = []
            for subform in self.formset.forms:
                # override the DELETE field to have a hidden input
                subform.fields[DELETION_FIELD_NAME].widget = forms.HiddenInput()

                # ditto for the ORDER field, if present
                if self.formset.can_order:
                    subform.fields[ORDERING_FIELD_NAME].widget = forms.HiddenInput()

                self.children.append(
                    self.child_edit_handler.get_bound_panel(
                        instance=subform.instance, request=self.request, form=subform
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
                instance=empty_form.instance, request=self.request, form=empty_form
            )

        def get_comparison(self):
            field_comparisons = []

            for panel in self.panel.child_edit_handler.children:
                field_comparisons.extend(
                    panel.get_bound_panel(
                        instance=None, request=self.request, form=None
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
        updated_kwargs = {
            "children": [
                FieldRowPanel(
                    [
                        FieldPanel("go_live_at"),
                        FieldPanel("expire_at"),
                    ],
                    classname="label-above",
                ),
            ],
            "heading": gettext_lazy("Scheduled publishing"),
            "classname": "publishing",
        }
        updated_kwargs.update(kwargs)
        super().__init__(**updated_kwargs)


class PrivacyModalPanel(Panel):
    def __init__(self, **kwargs):
        updated_kwargs = {"heading": gettext_lazy("Privacy"), "classname": "privacy"}
        updated_kwargs.update(kwargs)
        super().__init__(**updated_kwargs)

    class BoundPanel(Panel.BoundPanel):
        template_name = "wagtailadmin/pages/privacy_switch_panel.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            context["page"] = self.instance
            context["request"] = self.request
            return context

        @cached_property
        def media(self):
            return Media(js=[versioned_static("wagtailadmin/js/privacy-switch.js")])


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


# Now that we've defined panels, we can set up wagtailcore.Page to have some.
def set_default_page_edit_handlers(cls):
    cls.content_panels = [
        FieldPanel("title", classname="full title"),
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
        PrivacyModalPanel(),
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
                ObjectList(
                    cls.settings_panels,
                    heading=gettext_lazy("Settings"),
                    classname="settings",
                )
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
            "wagtail.admin.edit_handlers.StreamFieldPanel is obsolete and should be replaced by wagtail.admin.panels.FieldPanel",
            category=RemovedInWagtail50Warning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
