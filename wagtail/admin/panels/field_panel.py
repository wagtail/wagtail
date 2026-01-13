import functools

from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db.models import ForeignKey
from django.forms.models import ModelChoiceIterator
from django.template.loader import get_template
from django.utils.functional import cached_property
from django.utils.text import capfirst

from wagtail.admin import compare
from wagtail.admin.forms.models import registry as model_field_registry
from wagtail.admin.telepath import register as register_telepath_adapter
from wagtail.blocks import BlockField

from .base import Panel


class FieldPanel(Panel):
    TEMPLATE_VAR = "field_panel"
    read_only_output_template_name = "wagtailadmin/panels/read_only_output.html"

    def __init__(
        self,
        field_name,
        widget=None,
        disable_comments=None,
        permission=None,
        read_only=False,
        required_on_save=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.field_name = field_name
        self.widget = widget
        self.disable_comments = disable_comments
        self.permission = permission
        self.read_only = read_only
        self.required_on_save = required_on_save

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        kwargs.update(
            field_name=self.field_name,
            widget=self.widget,
            disable_comments=self.disable_comments,
            permission=self.permission,
            read_only=self.read_only,
            required_on_save=self.required_on_save,
        )
        return kwargs

    def get_form_options(self):
        if self.read_only:
            return {}

        opts = {
            "fields": [self.field_name],
        }

        required_on_save = self.required_on_save
        if required_on_save is None:
            # If required_on_save is not explicitly set, treat it as false unless:
            # - it corresponds to a model field with required_on_save=True (such as page title)
            # - it corresponds to a non-null, non-text-typed model field (in which case a blank value
            #   is not valid at the database level)
            try:
                db_field = self.db_field
            except FieldDoesNotExist:
                required_on_save = False
            else:
                required_on_save = getattr(db_field, "required_on_save", False) or (
                    db_field.null is False
                    and db_field.get_internal_type()
                    not in ("CharField", "TextField", "JSONField")
                )

        if not required_on_save:
            opts["defer_required_on_fields"] = [self.field_name]

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
        if self.model is None:
            raise ImproperlyConfigured(
                "%r must be bound to a model before calling db_field" % self
            )

        return self.model._meta.get_field(self.field_name)

    @property
    def clean_name(self):
        return self.field_name

    def format_value_for_display(self, value):
        """
        Overrides ``Panel.format_value_for_display()`` to add additional treatment
        for choice fields.
        """

        # NOTE: We look for formfield.choices over db_field.choices here,
        # as more field types can benefit that way.
        choices = getattr(self.db_field.formfield(), "choices", None)
        if not isinstance(choices, ModelChoiceIterator) and choices:
            labels = dict(choices)
            display_values = [
                str(labels.get(v, v))  # Use raw value if no match found
                for v in (
                    # Account for single AND multiple choice fields
                    tuple(value) if isinstance(value, (list, tuple)) else (value,)
                )
            ]
            return ", ".join(display_values)

        return super().format_value_for_display(value)

    def __repr__(self):
        return "<{} '{}' with model={}>".format(
            self.__class__.__name__,
            self.field_name,
            self.model,
        )

    @register_telepath_adapter
    class BoundPanel(Panel.BoundPanel):
        template_name = "wagtailadmin/panels/field_panel.html"
        # Default icons for common model field types,
        # based on the corresponding FieldBlock's icon.
        default_field_icons = {
            "DateField": "date",
            "TimeField": "time",
            "DateTimeField": "date",
            "URLField": "link-external",
            "TaggableManager": "tag",
            "EmailField": "mail",
            "TextField": "pilcrow",
            "RichTextField": "pilcrow",
            "FloatField": "decimal",
            "DecimalField": "decimal",
            "BooleanField": "tick-inverse",
        }

        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            self.bound_field = None
            self.read_only = False

            if self.form is None:
                return

            try:
                self.bound_field = self.form[self.field_name]
            except KeyError:
                if self.panel.read_only:
                    self.read_only = True
                    # Ensure heading and help_text are set to something useful
                    self.heading = self.panel.heading or capfirst(
                        self.panel.db_field.verbose_name
                    )
                    self.help_text = self.panel.help_text or capfirst(
                        self.panel.db_field.help_text
                    )
                return

            # Ensure heading and help_text are consistent across
            # Panel, BoundPanel and Field
            if self.panel.heading:
                self.heading = self.bound_field.label = self.panel.heading
            else:
                self.heading = self.bound_field.label

            self.help_text = self.panel.help_text or self.bound_field.help_text

        @property
        def field_name(self):
            return self.panel.field_name

        def is_shown(self):
            if (
                self.form is not None
                and self.bound_field is None
                and not self.read_only
            ):
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
            if self.bound_field is None:
                return False
            return self.bound_field.field.required

        def classes(self):
            classes = self.panel.classes()
            if self.bound_field and isinstance(self.bound_field.field, BlockField):
                classes.append("w-panel--nested")
            return classes

        @property
        def icon(self):
            """
            Display a different icon depending on the field's type.
            """
            # If the panel has an icon, use that.
            if self.panel.icon:
                return self.panel.icon

            # Try to use the model field first, then the form field because it's
            # possible to use FieldPanel without a model field by using a custom
            # form class.
            try:
                field = self.panel.db_field
            except FieldDoesNotExist:
                # The defined default icons are for model fields, but most of them
                # have a corresponding form field with the same name, so we just
                # hope the name matches.
                field = self.bound_field.field

            field_type = type(field)

            # ForeignKey fields can have a custom icon defined in the form field's widget
            # (e.g. page, image, and document choosers). If there's an overridden widget
            # with an icon attribute, use that.
            if issubclass(field_type, ForeignKey):
                overrides = model_field_registry.get(field) or {}
                widget = overrides.get("widget", None)
                return getattr(widget, "icon", None)

            # Otherwise, find a default icon based on the field's class or superclasses.
            for field_class in field_type.mro():
                field_name = field_class.__name__
                if field_name in self.default_field_icons:
                    return self.default_field_icons[field_name]

            return None

        def id_for_label(self):
            if self.read_only:
                return self.prefix
            return self.bound_field.id_for_label

        @property
        def comments_enabled(self):
            if self.panel.disable_comments is None and not self.read_only:
                # by default, enable comments on all fields except StreamField (which has its own comment handling)
                return not isinstance(self.bound_field.field, BlockField)
            else:
                return not self.panel.disable_comments

        @cached_property
        def value_from_instance(self):
            return getattr(self.instance, self.field_name)

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            if self.read_only:
                context.update(self.get_read_only_context_data())
            else:
                context.update(self.get_editable_context_data())
            return context

        def get_editable_context_data(self):
            widget_described_by_ids = []
            help_text_id = "%s-helptext" % self.prefix
            error_message_id = "%s-errors" % self.prefix
            wrapper_id = "%s-wrapper" % self.prefix

            widget_described_by_ids = []
            if self.help_text:
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

            return {
                "field": self.bound_field,
                "rendered_field": rendered_field,
                "error_message_id": error_message_id,
                "wrapper_id": wrapper_id,
                "help_text": self.help_text,
                "help_text_id": help_text_id,
                "show_add_comment_button": self.comments_enabled
                and getattr(
                    self.bound_field.field.widget,
                    "show_add_comment_button",
                    True,
                ),
            }

        def get_read_only_context_data(self):
            # Define context data for BoundPanel AND read-only output rendering
            context = {
                "id_for_label": self.id_for_label(),
                "help_text_id": "%s-helptext" % self.prefix,
                "help_text": self.help_text,
                "show_add_comment_button": self.comments_enabled,
                "raw_value": self.value_from_instance,
                "display_value": self.panel.format_value_for_display(
                    self.value_from_instance
                ),
            }

            # Render read-only output
            template = get_template(self.panel.read_only_output_template_name)
            rendered_field = template.render(context)

            # Add rendered output to BoundPanel context data
            context["rendered_field"] = rendered_field
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
            return "<{} '{}' with model={} instance={} request={} form={}>".format(
                self.__class__.__name__,
                self.field_name,
                self.panel.model,
                self.instance,
                self.request,
                self.form.__class__.__name__,
            )

        telepath_adapter_name = "wagtail.panels.FieldPanel"

        def js_opts(self):
            opts = super().js_opts()
            opts.update(
                {
                    "fieldName": self.field_name,
                    "widget": self.bound_field and self.bound_field.field.widget,
                }
            )
            return opts
