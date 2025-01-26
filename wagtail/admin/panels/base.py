from django.core.exceptions import ImproperlyConfigured
from django.utils.safestring import mark_safe

from wagtail.admin.forms.models import (
    WagtailAdminDraftStateFormMixin,
    WagtailAdminModelForm,
)
from wagtail.admin.ui.components import Component
from wagtail.blocks import StreamValue
from wagtail.coreutils import safe_snake_case
from wagtail.models import DraftStateMixin
from wagtail.rich_text import RichText
from wagtail.utils.text import text_from_html


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

    # The kwargs passed here are expected to come from Panel.get_form_options, which collects
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
    bases = [form_class]
    if issubclass(model, DraftStateMixin):
        bases.insert(0, WagtailAdminDraftStateFormMixin)
    return metaclass(class_name, tuple(bases), form_class_attrs)


class Panel:
    """
    Defines part (or all) of the edit form interface for pages and other models
    within the Wagtail admin. Each model has an associated top-level panel definition
    (also known as an edit handler), consisting of a nested structure of ``Panel`` objects.
    This provides methods for obtaining a :class:`~django.forms.ModelForm` subclass,
    with the field list and other parameters collated from all panels in the structure.
    It then handles rendering that form as HTML.

    The following parameters can be used to customize how the panel is displayed.
    For more details, see :ref:`customizing_panels`.

    :param heading: The heading text to display for the panel.
    :param classname: A CSS class name to add to the panel's HTML element.
    :param help_text: Help text to display within the panel.
    :param base_form_class: The base form class to use for the panel. Defaults to the model's ``base_form_class``, before falling back to :class:`~wagtail.admin.forms.WagtailAdminModelForm`. This is only relevant for the top-level panel.
    :param icon: The name of the icon to display next to the panel heading.
    :param attrs: A dictionary of HTML attributes to add to the panel's HTML element.
    """

    BASE_ATTRS = {}

    def __init__(
        self,
        heading="",
        classname="",
        help_text="",
        base_form_class=None,
        icon="",
        attrs=None,
    ):
        self.heading = heading
        self.classname = classname
        self.help_text = help_text
        self.base_form_class = base_form_class
        self.icon = icon
        self.model = None
        self.attrs = self.BASE_ATTRS.copy()

        if attrs is not None:
            self.attrs.update(attrs)

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
            "icon": self.icon,
            "attrs": self.attrs,
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
        return {}

    def get_form_class(self):
        """
        Construct a form class that has all the fields and formsets named in
        the children of this edit handler.
        """
        form_options = self.get_form_options()
        # If a custom form class was passed to the panel, use it.
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

    def get_bound_panel(self, instance=None, request=None, form=None, prefix="panel"):
        """
        Return a ``BoundPanel`` instance that can be rendered onto the template as a component. By default, this creates an instance
        of the panel class's inner ``BoundPanel`` class, which must inherit from ``Panel.BoundPanel``.
        """
        if self.model is None:
            raise ImproperlyConfigured(
                "%s.bind_to_model(model) must be called before get_bound_panel"
                % type(self).__name__
            )

        if not issubclass(self.BoundPanel, Panel.BoundPanel):
            raise ImproperlyConfigured(
                "%s.BoundPanel must be a subclass of Panel.BoundPanel"
                % type(self).__name__
            )

        return self.BoundPanel(
            panel=self, instance=instance, request=request, form=form, prefix=prefix
        )

    def on_model_bound(self):
        """
        Called after the panel has been associated with a model class and the ``self.model`` attribute is available;
        panels can override this method to perform additional initialisation related to the model.
        """
        pass

    def __repr__(self):
        return "<{} with model={}>".format(
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

    def id_for_label(self):
        """
        The ID to be used as the 'for' attribute of any <label> elements that refer
        to this object but are rendered outside of it. Leave blank if this object does not render
        as a single input field.
        """
        return ""

    @property
    def clean_name(self):
        """
        A name for this panel, consisting only of ASCII alphanumerics and underscores, suitable for use in identifiers.
        Usually generated from the panel heading. Note that this is not guaranteed to be unique or non-empty; anything
        making use of this and requiring uniqueness should validate and modify the return value as needed.
        """
        return safe_snake_case(self.heading)

    def format_value_for_display(self, value):
        """
        Hook to allow formatting of raw field values (and other attribute values) for human-readable
        display. For example, if rendering a ``RichTextField`` value, you might extract text from the HTML
        to generate a safer display value.
        """
        # Improve representation of many-to-many values
        if callable(getattr(value, "all", "")):
            return ", ".join(str(obj) for obj in value.all()) or "None"

        # Avoid rendering potentially unsafe HTML mid-form
        if isinstance(value, (RichText, StreamValue)):
            return text_from_html(value)

        return value

    class BoundPanel(Component):
        """
        A template component for a panel that has been associated with a model instance, form, and request.
        """

        def __init__(self, panel, instance, request, form, prefix):
            #: The panel definition corresponding to this bound panel
            self.panel = panel

            #: The model instance associated with this panel
            self.instance = instance

            #: The request object associated with this panel
            self.request = request

            #: The form object associated with this panel
            self.form = form

            #: A unique prefix for this panel, for use in HTML IDs
            self.prefix = prefix

            self.heading = self.panel.heading
            self.help_text = self.panel.help_text

        @property
        def classname(self):
            return self.panel.classname

        def classes(self):
            return self.panel.classes()

        @property
        def attrs(self):
            return self.panel.attrs

        @property
        def icon(self):
            return self.panel.icon

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

        def show_panel_furniture(self):
            """
            Whether this panel shows the panel furniture instead of being rendered outside of it.
            """
            return self.is_shown()

        def is_required(self):
            return False

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            context["self"] = self
            context["attrs"] = self.attrs
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
            return mark_safe(self.render_html() + self.render_missing_fields())

        def __repr__(self):
            return "<{} with model={} instance={} request={} form={}>".format(
                self.__class__.__name__,
                self.panel.model,
                self.instance,
                self.request,
                self.form.__class__.__name__,
            )
