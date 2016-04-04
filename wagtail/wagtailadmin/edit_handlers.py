from __future__ import unicode_literals

import django
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.forms.models import fields_for_model
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.six import text_type
from django.utils.translation import ugettext_lazy

from wagtail.wagtailadmin import widgets
from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.utils import (
    camelcase_to_underscore, resolve_model_string)

from wagtail.utils.decorators import cached_classmethod

# DIRECT_FORM_FIELD_OVERRIDES, FORM_FIELD_OVERRIDES are imported for backwards
# compatibility, as people are likely importing them from here and then
# appending their own overrides
from .forms import (  # NOQA
    DIRECT_FORM_FIELD_OVERRIDES, FORM_FIELD_OVERRIDES, WagtailAdminModelForm,
    WagtailAdminPageForm, formfield_for_dbfield)


def widget_with_script(widget, script):
    return mark_safe('{0}<script>{1}</script>'.format(widget, script))


def get_form_for_model(
    model, form_class=WagtailAdminModelForm,
    fields=None, exclude=None, formsets=None, exclude_formsets=None, widgets=None
):

    # django's modelform_factory with a bit of custom behaviour
    attrs = {'model': model}
    if fields is not None:
        attrs['fields'] = fields
    if exclude is not None:
        attrs['exclude'] = exclude
    if widgets is not None:
        attrs['widgets'] = widgets
    if formsets is not None:
        attrs['formsets'] = formsets
    if exclude_formsets is not None:
        attrs['exclude_formsets'] = exclude_formsets

    # Give this new form class a reasonable name.
    class_name = model.__name__ + str('Form')
    bases = (object,)
    if hasattr(form_class, 'Meta'):
        bases = (form_class.Meta,) + bases

    form_class_attrs = {
        'Meta': type(str('Meta'), bases, attrs)
    }

    metaclass = type(form_class)
    return metaclass(class_name, (form_class,), form_class_attrs)


def extract_panel_definitions_from_model_class(model, exclude=None):
    if hasattr(model, 'panels'):
        return model.panels

    panels = []

    _exclude = []
    if exclude:
        _exclude.extend(exclude)

    fields = fields_for_model(model, exclude=_exclude, formfield_callback=formfield_for_dbfield)

    for field_name, field in fields.items():
        try:
            panel_class = field.widget.get_panel()
        except AttributeError:
            panel_class = FieldPanel

        panel = panel_class(field_name)
        panels.append(panel)

    return panels


class EditHandler(object):
    """
    Abstract class providing sensible default behaviours for objects implementing
    the EditHandler API
    """

    # return list of widget overrides that this EditHandler wants to be in place
    # on the form it receives
    @classmethod
    def widget_overrides(cls):
        return {}

    # return list of fields that this EditHandler expects to find on the form
    @classmethod
    def required_fields(cls):
        return []

    # return a dict of formsets that this EditHandler requires to be present
    # as children of the ClusterForm; the dict is a mapping from relation name
    # to parameters to be passed as part of get_form_for_model's 'formsets' kwarg
    @classmethod
    def required_formsets(cls):
        return {}

    # return any HTML that needs to be output on the edit page once per edit handler definition.
    # Typically this will be used to define snippets of HTML within <script type="text/x-template"></script> blocks
    # for Javascript code to work with.
    @classmethod
    def html_declarations(cls):
        return ''

    def __init__(self, instance=None, form=None):
        if not instance:
            raise ValueError("EditHandler did not receive an instance object")
        self.instance = instance

        if not form:
            raise ValueError("EditHandler did not receive a form object")
        self.form = form

    # Heading / help text to display to the user
    heading = ""
    help_text = ""

    def classes(self):
        """
        Additional CSS classnames to add to whatever kind of object this is at output.
        Subclasses of EditHandler should override this, invoking super(B, self).classes() to
        append more classes specific to the situation.
        """

        classes = []

        try:
            classes.append(self.classname)
        except AttributeError:
            pass

        return classes

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

    def render_as_object(self):
        """
        Render this object as it should appear within an ObjectList. Should not
        include the <h2> heading or help text - ObjectList will supply those
        """
        # by default, assume that the subclass provides a catch-all render() method
        return self.render()

    def render_as_field(self):
        """
        Render this object as it should appear within a <ul class="fields"> list item
        """
        # by default, assume that the subclass provides a catch-all render() method
        return self.render()

    def render_missing_fields(self):
        """
        Helper function: render all of the fields that are defined on the form but not "claimed" by
        any panels via required_fields. These fields are most likely to be hidden fields introduced
        by the forms framework itself, such as ORDER / DELETE fields on formset members.

        (If they aren't actually hidden fields, then they will appear as ugly unstyled / label-less fields
        outside of the panel furniture. But there's not much we can do about that.)
        """
        rendered_fields = self.required_fields()
        missing_fields_html = [
            text_type(self.form[field_name])
            for field_name in self.form.fields
            if field_name not in rendered_fields
        ]

        return mark_safe(''.join(missing_fields_html))

    def render_form_content(self):
        """
        Render this as an 'object', ensuring that all fields necessary for a valid form
        submission are included
        """
        return mark_safe(self.render_as_object() + self.render_missing_fields())


class BaseCompositeEditHandler(EditHandler):
    """
    Abstract class for EditHandlers that manage a set of sub-EditHandlers.
    Concrete subclasses must attach a 'children' property
    """
    _widget_overrides = None

    @classmethod
    def widget_overrides(cls):
        if cls._widget_overrides is None:
            # build a collated version of all its children's widget lists
            widgets = {}
            for handler_class in cls.children:
                widgets.update(handler_class.widget_overrides())
            cls._widget_overrides = widgets

        return cls._widget_overrides

    _required_fields = None

    @classmethod
    def required_fields(cls):
        if cls._required_fields is None:
            fields = []
            for handler_class in cls.children:
                fields.extend(handler_class.required_fields())
            cls._required_fields = fields

        return cls._required_fields

    _required_formsets = None

    @classmethod
    def required_formsets(cls):
        if cls._required_formsets is None:
            formsets = {}
            for handler_class in cls.children:
                formsets.update(handler_class.required_formsets())
            cls._required_formsets = formsets

        return cls._required_formsets

    @classmethod
    def html_declarations(cls):
        return mark_safe(''.join([c.html_declarations() for c in cls.children]))

    def __init__(self, instance=None, form=None):
        super(BaseCompositeEditHandler, self).__init__(instance=instance, form=form)

        self.children = [
            handler_class(instance=self.instance, form=self.form)
            for handler_class in self.__class__.children
        ]

    def render(self):
        return mark_safe(render_to_string(self.template, {
            'self': self
        }))


class BaseFormEditHandler(BaseCompositeEditHandler):
    """
    Base class for edit handlers that can construct a form class for all their
    child edit handlers.
    """

    # The form class used as the base for constructing specific forms for this
    # edit handler.  Subclasses can override this attribute to provide a form
    # with custom validation, for example.  Custom forms must subclass
    # WagtailAdminModelForm
    base_form_class = None

    _form_class = None

    @classmethod
    def get_form_class(cls, model):
        """
        Construct a form class that has all the fields and formsets named in
        the children of this edit handler.
        """
        if cls._form_class is None:
            # If a custom form class was passed to the EditHandler, use it.
            # Otherwise, use the base_form_class from the model.
            # If that is not defined, use WagtailAdminModelForm.
            model_form_class = getattr(model, 'base_form_class', WagtailAdminModelForm)
            base_form_class = cls.base_form_class or model_form_class

            cls._form_class = get_form_for_model(
                model,
                form_class=base_form_class,
                fields=cls.required_fields(),
                formsets=cls.required_formsets(),
                widgets=cls.widget_overrides())
        return cls._form_class


class BaseTabbedInterface(BaseFormEditHandler):
    template = "wagtailadmin/edit_handlers/tabbed_interface.html"


class TabbedInterface(object):
    def __init__(self, children, base_form_class=None):
        self.children = children
        self.base_form_class = base_form_class

    def bind_to_model(self, model):
        return type(str('_TabbedInterface'), (BaseTabbedInterface,), {
            'model': model,
            'children': [child.bind_to_model(model) for child in self.children],
            'base_form_class': self.base_form_class,
        })


class BaseObjectList(BaseFormEditHandler):
    template = "wagtailadmin/edit_handlers/object_list.html"


class ObjectList(object):

    def __init__(self, children, heading="", classname="",
                 base_form_class=None):
        self.children = children
        self.heading = heading
        self.classname = classname
        self.base_form_class = base_form_class

    def bind_to_model(self, model):
        return type(str('_ObjectList'), (BaseObjectList,), {
            'model': model,
            'children': [child.bind_to_model(model) for child in self.children],
            'heading': self.heading,
            'classname': self.classname,
            'base_form_class': self.base_form_class,
        })


class BaseFieldRowPanel(BaseCompositeEditHandler):
    template = "wagtailadmin/edit_handlers/field_row_panel.html"


class FieldRowPanel(object):
    def __init__(self, children, classname=""):
        self.children = children
        self.classname = classname

    def bind_to_model(self, model):
        return type(str('_FieldRowPanel'), (BaseFieldRowPanel,), {
            'model': model,
            'children': [child.bind_to_model(model) for child in self.children],
            'classname': self.classname,
        })


class BaseMultiFieldPanel(BaseCompositeEditHandler):
    template = "wagtailadmin/edit_handlers/multi_field_panel.html"

    def classes(self):
        classes = super(BaseMultiFieldPanel, self).classes()
        classes.append("multi-field")

        return classes


class MultiFieldPanel(object):
    def __init__(self, children, heading="", classname=""):
        self.children = children
        self.heading = heading
        self.classname = classname

    def bind_to_model(self, model):
        return type(str('_MultiFieldPanel'), (BaseMultiFieldPanel,), {
            'model': model,
            'children': [child.bind_to_model(model) for child in self.children],
            'heading': self.heading,
            'classname': self.classname,
        })


class BaseFieldPanel(EditHandler):

    TEMPLATE_VAR = 'field_panel'

    @classmethod
    def widget_overrides(cls):
        """check if a specific widget has been defined for this field"""
        if hasattr(cls, 'widget'):
            return {cls.field_name: cls.widget}
        else:
            return {}

    def __init__(self, instance=None, form=None):
        super(BaseFieldPanel, self).__init__(instance=instance, form=form)
        self.bound_field = self.form[self.field_name]

        self.heading = self.bound_field.label
        self.help_text = self.bound_field.help_text

    def classes(self):
        classes = super(BaseFieldPanel, self).classes()

        if self.bound_field.field.required:
            classes.append("required")
        if self.bound_field.errors:
            classes.append("error")

        classes.append(self.field_type())

        return classes

    def field_type(self):
        return camelcase_to_underscore(self.bound_field.field.__class__.__name__)

    def id_for_label(self):
        return self.bound_field.id_for_label

    object_template = "wagtailadmin/edit_handlers/single_field_panel.html"

    def render_as_object(self):
        return mark_safe(render_to_string(self.object_template, {
            'self': self,
            self.TEMPLATE_VAR: self,
            'field': self.bound_field,
        }))

    field_template = "wagtailadmin/edit_handlers/field_panel_field.html"

    def render_as_field(self):
        context = {
            'field': self.bound_field,
            'field_type': self.field_type(),
        }
        return mark_safe(render_to_string(self.field_template, context))

    @classmethod
    def required_fields(self):
        return [self.field_name]


class FieldPanel(object):
    def __init__(self, field_name, classname="", widget=None):
        self.field_name = field_name
        self.classname = classname
        self.widget = widget

    def bind_to_model(self, model):
        base = {
            'model': model,
            'field_name': self.field_name,
            'classname': self.classname,
        }

        if self.widget:
            base['widget'] = self.widget

        return type(str('_FieldPanel'), (BaseFieldPanel,), base)


class BaseRichTextFieldPanel(BaseFieldPanel):
    pass


class RichTextFieldPanel(object):
    def __init__(self, field_name):
        self.field_name = field_name

    def bind_to_model(self, model):
        return type(str('_RichTextFieldPanel'), (BaseRichTextFieldPanel,), {
            'model': model,
            'field_name': self.field_name,
        })


class BaseChooserPanel(BaseFieldPanel):
    """
    Abstract superclass for panels that provide a modal interface for choosing (or creating)
    a database object such as an image, resulting in an ID that is used to populate
    a hidden foreign key input.

    Subclasses provide:
    * field_template (only required if the default template of field_panel_field.html is not usable)
    * object_type_name - something like 'image' which will be used as the var name
      for the object instance in the field_template
    """

    def get_chosen_item(self):
        field = self.instance._meta.get_field(self.field_name)
        related_model = field.rel.model
        try:
            return getattr(self.instance, self.field_name)
        except related_model.DoesNotExist:
            # if the ForeignKey is null=False, Django decides to raise
            # a DoesNotExist exception here, rather than returning None
            # like every other unpopulated field type. Yay consistency!
            return None

    def render_as_field(self):
        instance_obj = self.get_chosen_item()
        context = {
            'field': self.bound_field,
            self.object_type_name: instance_obj,
            'is_chosen': bool(instance_obj),  # DEPRECATED - passed to templates for backwards compatibility only
        }
        return mark_safe(render_to_string(self.field_template, context))


class BasePageChooserPanel(BaseChooserPanel):
    object_type_name = "page"

    @classmethod
    def widget_overrides(cls):
        return {cls.field_name: widgets.AdminPageChooser(
            target_models=cls.target_models(),
            can_choose_root=cls.can_choose_root)}

    @cached_classmethod
    def target_models(cls):
        if cls.page_type:
            target_models = []

            for page_type in cls.page_type:
                try:
                    target_models.append(resolve_model_string(page_type))
                except LookupError:
                    raise ImproperlyConfigured(
                        "{0}.page_type must be of the form 'app_label.model_name', given {1!r}".format(
                            cls.__name__, page_type
                        )
                    )
                except ValueError:
                    raise ImproperlyConfigured(
                        "{0}.page_type refers to model {1!r} that has not been installed".format(
                            cls.__name__, page_type
                        )
                    )

            return target_models
        else:
            return [cls.model._meta.get_field(cls.field_name).rel.to]

    @cached_classmethod
    def target_content_type(cls):
        return list(ContentType.objects.get_for_models(*cls.target_models()).values())


class PageChooserPanel(object):
    def __init__(self, field_name, page_type=None, can_choose_root=False):
        self.field_name = field_name

        if page_type:
            # Convert single string/model into list
            if not isinstance(page_type, (list, tuple)):
                page_type = [page_type]
        else:
            page_type = []

        self.page_type = page_type
        self.can_choose_root = can_choose_root

    def bind_to_model(self, model):
        return type(str('_PageChooserPanel'), (BasePageChooserPanel,), {
            'model': model,
            'field_name': self.field_name,
            'page_type': self.page_type,
            'can_choose_root': self.can_choose_root,
        })


class BaseInlinePanel(EditHandler):
    @classmethod
    def get_panel_definitions(cls):
        # Look for a panels definition in the InlinePanel declaration
        if cls.panels is not None:
            return cls.panels
        # Failing that, get it from the model
        else:
            return extract_panel_definitions_from_model_class(
                cls.related.related_model,
                exclude=[cls.related.field.name]
            )

    _child_edit_handler_class = None

    @classmethod
    def get_child_edit_handler_class(cls):
        if cls._child_edit_handler_class is None:
            panels = cls.get_panel_definitions()
            cls._child_edit_handler_class = MultiFieldPanel(
                panels,
                heading=cls.heading
            ).bind_to_model(cls.related.related_model)

        return cls._child_edit_handler_class

    @classmethod
    def required_formsets(cls):
        child_edit_handler_class = cls.get_child_edit_handler_class()
        return {
            cls.relation_name: {
                'fields': child_edit_handler_class.required_fields(),
                'widgets': child_edit_handler_class.widget_overrides(),
                'min_num': cls.min_num,
                'validate_min': cls.min_num is not None,
                'max_num': cls.max_num,
                'validate_max': cls.max_num is not None
            }
        }

    def __init__(self, instance=None, form=None):
        super(BaseInlinePanel, self).__init__(instance=instance, form=form)

        self.formset = form.formsets[self.__class__.relation_name]

        child_edit_handler_class = self.__class__.get_child_edit_handler_class()
        self.children = []
        for subform in self.formset.forms:
            # override the DELETE field to have a hidden input
            subform.fields['DELETE'].widget = forms.HiddenInput()

            # ditto for the ORDER field, if present
            if self.formset.can_order:
                subform.fields['ORDER'].widget = forms.HiddenInput()

            self.children.append(
                child_edit_handler_class(instance=subform.instance, form=subform)
            )

        # if this formset is valid, it may have been re-ordered; respect that
        # in case the parent form errored and we need to re-render
        if self.formset.can_order and self.formset.is_valid():
            self.children = sorted(self.children, key=lambda x: x.form.cleaned_data['ORDER'])

        empty_form = self.formset.empty_form
        empty_form.fields['DELETE'].widget = forms.HiddenInput()
        if self.formset.can_order:
            empty_form.fields['ORDER'].widget = forms.HiddenInput()

        self.empty_child = child_edit_handler_class(instance=empty_form.instance, form=empty_form)

    template = "wagtailadmin/edit_handlers/inline_panel.html"

    def render(self):
        formset = render_to_string(self.template, {
            'self': self,
            'can_order': self.formset.can_order,
        })
        js = self.render_js_init()
        return widget_with_script(formset, js)

    js_template = "wagtailadmin/edit_handlers/inline_panel.js"

    def render_js_init(self):
        return mark_safe(render_to_string(self.js_template, {
            'self': self,
            'can_order': self.formset.can_order,
        }))


class InlinePanel(object):
    def __init__(self, relation_name, panels=None, label='', help_text='', min_num=None, max_num=None):
        self.relation_name = relation_name
        self.panels = panels
        self.label = label
        self.help_text = help_text
        self.min_num = min_num
        self.max_num = max_num

    def bind_to_model(self, model):
        if django.VERSION >= (1, 9):
            related = getattr(model, self.relation_name).rel
        else:
            related = getattr(model, self.relation_name).related

        return type(str('_InlinePanel'), (BaseInlinePanel,), {
            'model': model,
            'relation_name': self.relation_name,
            'related': related,
            'panels': self.panels,
            'heading': self.label,
            'help_text': self.help_text,
            # TODO: can we pick this out of the foreign key definition as an alternative?
            # (with a bit of help from the inlineformset object, as we do for label/heading)
            'min_num': self.min_num,
            'max_num': self.max_num
        })


# This allows users to include the publishing panel in their own per-model override
# without having to write these fields out by hand, potentially losing 'classname'
# and therefore the associated styling of the publishing panel
def PublishingPanel():
    return MultiFieldPanel([
        FieldRowPanel([
            FieldPanel('go_live_at'),
            FieldPanel('expire_at'),
        ], classname="label-above"),
    ], ugettext_lazy('Scheduled publishing'), classname="publishing")


# Now that we've defined EditHandlers, we can set up wagtailcore.Page to have some.
Page.content_panels = [
    FieldPanel('title', classname="full title"),
]

Page.promote_panels = [
    MultiFieldPanel([
        FieldPanel('slug'),
        FieldPanel('seo_title'),
        FieldPanel('show_in_menus'),
        FieldPanel('search_description'),
    ], ugettext_lazy('Common page configuration')),
]

Page.settings_panels = [
    PublishingPanel()
]

Page.base_form_class = WagtailAdminPageForm


@cached_classmethod
def get_edit_handler(cls):
    """
    Get the EditHandler to use in the Wagtail admin when editing this page type.
    """
    if hasattr(cls, 'edit_handler'):
        return cls.edit_handler.bind_to_model(cls)

    # construct a TabbedInterface made up of content_panels, promote_panels
    # and settings_panels, skipping any which are empty
    tabs = []

    if cls.content_panels:
        tabs.append(ObjectList(cls.content_panels, heading=ugettext_lazy('Content')))
    if cls.promote_panels:
        tabs.append(ObjectList(cls.promote_panels, heading=ugettext_lazy('Promote')))
    if cls.settings_panels:
        tabs.append(ObjectList(cls.settings_panels, heading=ugettext_lazy('Settings'), classname="settings"))

    EditHandler = TabbedInterface(tabs, base_form_class=cls.base_form_class)
    return EditHandler.bind_to_model(cls)


Page.get_edit_handler = get_edit_handler


class BaseStreamFieldPanel(BaseFieldPanel):
    def classes(self):
        classes = super(BaseStreamFieldPanel, self).classes()
        classes.append("stream-field")

        # In case of a validation error, BlockWidget will take care of outputting the error on the
        # relevant sub-block, so we don't want the stream block as a whole to be wrapped in an 'error' class.
        if 'error' in classes:
            classes.remove("error")

        return classes

    @classmethod
    def html_declarations(cls):
        return cls.block_def.all_html_declarations()

    def id_for_label(self):
        # a StreamField may consist of many input fields, so it's not meaningful to
        # attach the label to any specific one
        return ""


class StreamFieldPanel(object):
    def __init__(self, field_name):
        self.field_name = field_name

    def bind_to_model(self, model):
        return type(str('_StreamFieldPanel'), (BaseStreamFieldPanel,), {
            'model': model,
            'field_name': self.field_name,
            'block_def': model._meta.get_field(self.field_name).stream_block
        })
