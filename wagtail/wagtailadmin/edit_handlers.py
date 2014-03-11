import copy
import re
import datetime

from taggit.forms import TagWidget
from modelcluster.forms import ClusterForm, ClusterFormMetaclass

from django.template.loader import render_to_string
from django.template.defaultfilters import addslashes
from django.utils.safestring import mark_safe
from django import forms
from django.db import models
from django.forms.models import fields_for_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ImproperlyConfigured, ValidationError
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.translation import ugettext as _, ugettext_lazy as __

from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.util import camelcase_to_underscore
from wagtail.wagtailcore.fields import RichTextArea


class FriendlyDateInput(forms.DateInput):
    """
    A custom DateInput widget that formats dates as "05 Oct 2013"
    and adds class="friendly_date" to be picked up by jquery datepicker.
    """
    def __init__(self, attrs=None):
        default_attrs = {'class': 'friendly_date'}
        if attrs:
            default_attrs.update(attrs)

        super(FriendlyDateInput, self).__init__(attrs=default_attrs, format='%d %b %Y')


class FriendlyTimeInput(forms.TimeInput):
    """
    A custom TimeInput widget that formats dates as "5.30pm"
    and adds class="friendly_time" to be picked up by jquery timepicker.
    """
    def __init__(self, attrs=None):
        default_attrs = {'class': 'friendly_time'}
        if attrs:
            default_attrs.update(attrs)

        super(FriendlyTimeInput, self).__init__(attrs=default_attrs, format='%I.%M%p')


class FriendlyTimeField(forms.CharField):
    def to_python(self, time_string):
        # Check if the string is blank
        if not time_string:
            return None

        # Look for time in the string
        expr = re.compile("^(?P<hour>\d+)(?:(?:.|:)(?P<minute>\d+))?(?P<am_pm>am|pm)")
        match = expr.match(time_string.lower())
        if match:
            # Pull out values from string
            hour_string, minute_string, am_pm = match.groups()

            # Convert hours and minutes to integers
            hour = int(hour_string)
            if minute_string:
                minute = int(minute_string)
            else:
                minute = 0

            # Create python time
            if am_pm == "pm" and hour < 12:
                hour += 12

            if am_pm == "am" and hour >= 12:
                hour -= 12

            return datetime.time(hour=hour, minute=minute)
        else:
            raise ValidationError(_("Please type a valid time"))
            

class LocalizedDateInput(forms.DateInput):
    """
    A custom DateInput widget that formats localized dates
    and adds class="friendly_date" to be picked up by jquery datepicker.
    """
    def __init__(self, attrs=None):
        default_attrs = {'class': 'localized_date', 'localize':True}
        if attrs:
            default_attrs.update(attrs)

        super(LocalizedDateInput, self).__init__(attrs=default_attrs)


class LocalizedTimeInput(forms.TimeInput):
    """
    A custom TimeInput widget that formats dates as "5.30pm"
    and adds class="friendly_time" to be picked up by jquery timepicker.
    """
    def __init__(self, attrs=None):
        default_attrs = {'class': 'localized_time'}
        if attrs:
            default_attrs.update(attrs)
        # Just use 24-hour format
        super(LocalizedTimeInput, self).__init__(attrs=default_attrs, format='%H:%M')


class LocalizedTimeField(forms.CharField):
    def to_python(self, time_string):
        # Check if the string is blank
        if not time_string:
            return None

        # Look for time in the string
        expr = re.compile("^(?P<hour>\d+)(?:(?:.|:)(?P<minute>\d+))?")
        match = expr.match(time_string.lower())
        if match:
            # Pull out values from string
            hour_string, minute_string= match.groups()

            # Convert hours and minutes to integers
            hour = int(hour_string)
            if minute_string:
                minute = int(minute_string)
            else:
                minute = 0
            if hour>=24 or hour < 0 or minute >=60 or minute < 0:
                raise ValidationError(_("Please type a valid time"))
                
            return datetime.time(hour=hour, minute=minute)
        else:
            raise ValidationError(_("Please type a valid time") )


if hasattr(settings, 'USE_L10N') and settings.USE_L10N==True:
    FORM_FIELD_OVERRIDES = {
        models.DateField: {'widget': LocalizedDateInput},
        models.TimeField: {'widget': LocalizedTimeInput, 'form_class': LocalizedTimeField},
    }
else: # Fall back to friendly date/time            
    FORM_FIELD_OVERRIDES = {
        models.DateField: {'widget': FriendlyDateInput},
        models.TimeField: {'widget': FriendlyTimeInput, 'form_class': FriendlyTimeField},
    }

WIDGET_JS = {
    FriendlyDateInput: (lambda id: "initFriendlyDateChooser(fixPrefix('%s'));" % id),
    FriendlyTimeInput: (lambda id: "initFriendlyTimeChooser(fixPrefix('%s'));" % id),
    LocalizedDateInput: (lambda id: "initLocalizedDateChooser(fixPrefix('%s'));" % id),
    LocalizedTimeInput: (lambda id: "initLocalizedTimeChooser(fixPrefix('%s'));" % id),
    RichTextArea: (lambda id: "makeRichTextEditable(fixPrefix('%s'));" % id),
    TagWidget: (
        lambda id: "initTagField(fixPrefix('%s'), '%s');" % (
            id, addslashes(reverse('wagtailadmin_tag_autocomplete'))
        )
    ),
}


# Callback to allow us to override the default form fields provided for each model field.
def formfield_for_dbfield(db_field, **kwargs):
    # snarfed from django/contrib/admin/options.py

    # If we've got overrides for the formfield defined, use 'em. **kwargs
    # passed to formfield_for_dbfield override the defaults.
    for klass in db_field.__class__.mro():
        if klass in FORM_FIELD_OVERRIDES:
            kwargs = dict(copy.deepcopy(FORM_FIELD_OVERRIDES[klass]), **kwargs)
            return db_field.formfield(**kwargs)

    # For any other type of field, just call its formfield() method.
    return db_field.formfield(**kwargs)


class WagtailAdminModelFormMetaclass(ClusterFormMetaclass):
    # Override the behaviour of the regular ModelForm metaclass -
    # which handles the translation of model fields to form fields -
    # to use our own formfield_for_dbfield function to do that translation.
    # This is done by sneaking a formfield_callback property into the class
    # being defined (unless the class already provides a formfield_callback
    # of its own).

    # while we're at it, we'll also set extra_form_count to 0, as we're creating
    # extra forms in JS
    extra_form_count = 0

    def __new__(cls, name, bases, attrs):
        if 'formfield_callback' not in attrs or attrs['formfield_callback'] is None:
            attrs['formfield_callback'] = formfield_for_dbfield

        new_class = super(WagtailAdminModelFormMetaclass, cls).__new__(cls, name, bases, attrs)
        return new_class

WagtailAdminModelForm = WagtailAdminModelFormMetaclass('WagtailAdminModelForm', (ClusterForm,), {})

# Now, any model forms built off WagtailAdminModelForm instead of ModelForm should pick up
# the nice form fields defined in FORM_FIELD_OVERRIDES.


def get_form_for_model(
    model,
    fields=None, exclude=None, formsets=None, exclude_formsets=None, widgets=None
):

    # django's modelform_factory with a bit of custom behaviour
    # (dealing with Treebeard's tree-related fields that really should have
    # been editable=False)
    attrs = {'model': model}

    if fields is not None:
        attrs['fields'] = fields

    if exclude is not None:
        attrs['exclude'] = exclude
    if issubclass(model, Page):
        attrs['exclude'] = attrs.get('exclude', []) + ['content_type', 'path', 'depth', 'numchild']

    if widgets is not None:
        attrs['widgets'] = widgets

    if formsets is not None:
        attrs['formsets'] = formsets

    if exclude_formsets is not None:
        attrs['exclude_formsets'] = exclude_formsets

    # Give this new form class a reasonable name.
    class_name = model.__name__ + str('Form')
    form_class_attrs = {
        'Meta': type('Meta', (object,), attrs)
    }

    return WagtailAdminModelFormMetaclass(class_name, (WagtailAdminModelForm,), form_class_attrs)


def extract_panel_definitions_from_model_class(model, exclude=None):
    if hasattr(model, 'panels'):
        return model.panels

    panels = []

    _exclude = []
    if exclude:
        _exclude.extend(exclude)
    if issubclass(model, Page):
        _exclude = ['content_type', 'path', 'depth', 'numchild']

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

    # return list of formset names that this EditHandler requires to be present
    # as children of the ClusterForm
    @classmethod
    def required_formsets(cls):
        return []

    # the top-level edit handler is responsible for providing a form class that can produce forms
    # acceptable to the edit handler
    _form_class = None

    @classmethod
    def get_form_class(cls, model):
        if cls._form_class is None:
            cls._form_class = get_form_for_model(
                model,
                formsets=cls.required_formsets(), widgets=cls.widget_overrides())
        return cls._form_class

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

    def object_classnames(self):
        """
        Additional classnames to add to the <li class="object"> when rendering this
        within an ObjectList
        """
        return ""

    def field_classnames(self):
        """
        Additional classnames to add to the <li> when rendering this within a
        <ul class="fields">
        """
        return ""

    def field_type(self):
        """
        The kind of field it is e.g boolean_field. Useful for better semantic markup of field display based on type
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

    def render_js(self):
        """
        Render a snippet of Javascript code to be executed when this object's rendered
        HTML is inserted into the DOM. (This won't necessarily happen on page load...)
        """
        return ""

    def rendered_fields(self):
        """
        return a list of the fields of the passed form which are rendered by this
        EditHandler.
        """
        return []

    def render_missing_fields(self):
        """
        Helper function: render all of the fields of the form that are not accounted for
        in rendered_fields
        """
        rendered_fields = self.rendered_fields()
        missing_fields_html = [
            unicode(self.form[field_name])
            for field_name in self.form.fields
            if field_name not in rendered_fields
        ]

        return mark_safe(u''.join(missing_fields_html))

    def render_form_content(self):
        """
        Render this as an 'object', along with any unaccounted-for fields to make this
        a valid submittable form
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

    _required_formsets = None

    @classmethod
    def required_formsets(cls):
        if cls._required_formsets is None:
            formsets = []
            for handler_class in cls.children:
                formsets.extend(handler_class.required_formsets())
            cls._required_formsets = formsets

        return cls._required_formsets

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

    def render_js(self):
        return mark_safe(u'\n'.join([handler.render_js() for handler in self.children]))

    def rendered_fields(self):
        result = []
        for handler in self.children:
            result += handler.rendered_fields()

        return result


class BaseTabbedInterface(BaseCompositeEditHandler):
    template = "wagtailadmin/edit_handlers/tabbed_interface.html"


def TabbedInterface(children):
    return type('_TabbedInterface', (BaseTabbedInterface,), {'children': children})


class BaseObjectList(BaseCompositeEditHandler):
    template = "wagtailadmin/edit_handlers/object_list.html"


def ObjectList(children, heading=""):
    return type('_ObjectList', (BaseObjectList,), {
        'children': children,
        'heading': heading,
    })


class BaseMultiFieldPanel(BaseCompositeEditHandler):
    template = "wagtailadmin/edit_handlers/multi_field_panel.html"


def MultiFieldPanel(children, heading=""):
    return type('_MultiFieldPanel', (BaseMultiFieldPanel,), {
        'children': children,
        'heading': heading,
    })


class BaseFieldPanel(EditHandler):
    def __init__(self, instance=None, form=None):
        super(BaseFieldPanel, self).__init__(instance=instance, form=form)
        self.bound_field = self.form[self.field_name]

        self.heading = self.bound_field.label
        self.help_text = self.bound_field.help_text

    def object_classnames(self):
        try:
            return "single-field " + self.classname
        except (AttributeError, TypeError):
            return "single-field"

    def field_type(self):
        return camelcase_to_underscore(self.bound_field.field.__class__.__name__)

    def field_classnames(self):
        classname = self.field_type()
        if self.bound_field.field.required:
            classname += " required"
        if self.bound_field.errors:
            classname += " error"

        return classname

    object_template = "wagtailadmin/edit_handlers/field_panel_object.html"

    def render_as_object(self):
        return mark_safe(render_to_string(self.object_template, {
            'self': self,
            'field_content': self.render_as_field(show_help_text=False),
        }))

    def render_js(self):
        try:
            # see if there's an entry for this widget type in WIDGET_JS
            js_func = WIDGET_JS[self.bound_field.field.widget.__class__]
        except KeyError:
            return ''

        return mark_safe(js_func(self.bound_field.id_for_label))

    field_template = "wagtailadmin/edit_handlers/field_panel_field.html"

    def render_as_field(self, show_help_text=True):
        return mark_safe(render_to_string(self.field_template, {
            'field': self.bound_field,
            'field_type': self.field_type(),
            'show_help_text': show_help_text,
        }))

    def rendered_fields(self):
        return [self.field_name]


def FieldPanel(field_name, classname=None):
    return type('_FieldPanel', (BaseFieldPanel,), {
        'field_name': field_name,
        'classname': classname,
    })


class BaseRichTextFieldPanel(BaseFieldPanel):
    def render_js(self):
        return mark_safe("makeRichTextEditable(fixPrefix('%s'));" % self.bound_field.id_for_label)


def RichTextFieldPanel(field_name):
    return type('_RichTextFieldPanel', (BaseRichTextFieldPanel,), {
        'field_name': field_name,
    })


class BaseChooserPanel(BaseFieldPanel):
    """
    Abstract superclass for panels that provide a modal interface for choosing (or creating)
    a database object such as an image, resulting in an ID that is used to populate
    a hidden foreign key input.

    Subclasses provide:
    * field_template
    * object_type_name - something like 'image' which will be used as the var name
      for the object instance in the field_template
    * js_function_name - a JS function responsible for the modal workflow; this receives
      the ID of the hidden field as a parameter, and should ultimately populate that field
      with the appropriate object ID. If the function requires any other parameters, the
      subclass will need to override render_js instead.
    """
    @classmethod
    def widget_overrides(cls):
        return {cls.field_name: forms.HiddenInput}

    def get_chosen_item(self):
        try:
            return getattr(self.instance, self.field_name)
        except ObjectDoesNotExist:
            # if the ForeignKey is null=False, Django decides to raise
            # a DoesNotExist exception here, rather than returning None
            # like every other unpopulated field type. Yay consistency!
            return None

    def render_as_field(self, show_help_text=True):
        instance_obj = self.get_chosen_item()
        return mark_safe(render_to_string(self.field_template, {
            'field': self.bound_field,
            self.object_type_name: instance_obj,
            'is_chosen': bool(instance_obj),
            'show_help_text': show_help_text,
        }))

    def render_js(self):
        return mark_safe("%s(fixPrefix('%s'));" % (self.js_function_name, self.bound_field.id_for_label))


class BasePageChooserPanel(BaseChooserPanel):
    field_template = "wagtailadmin/edit_handlers/page_chooser_panel.html"
    object_type_name = "page"

    _target_content_type = None

    @classmethod
    def target_content_type(cls):
        if cls._target_content_type is None:
            if cls.page_type:
                if isinstance(cls.page_type, basestring):
                    # translate the passed model name into an actual model class
                    from django.db.models import get_model
                    try:
                        app_label, model_name = cls.page_type.split('.')
                    except ValueError:
                        raise ImproperlyConfigured("The page_type passed to PageChooserPanel must be of the form 'app_label.model_name'")

                    page_type = get_model(app_label, model_name)
                    if page_type is None:
                        raise ImproperlyConfigured("PageChooserPanel refers to model '%s' that has not been installed" % cls.page_type)
                else:
                    page_type = cls.page_type

                cls._target_content_type = ContentType.objects.get_for_model(page_type)
            else:
                # TODO: infer the content type by introspection on the foreign key
                cls._target_content_type = ContentType.objects.get_by_natural_key('wagtailcore', 'page')

        return cls._target_content_type

    def render_js(self):
        page = self.get_chosen_item()
        parent = page.get_parent() if page else None
        content_type = self.__class__.target_content_type()

        return mark_safe("createPageChooser(fixPrefix('%s'), '%s.%s', %s);" % (
            self.bound_field.id_for_label,
            content_type.app_label,
            content_type.model,
            (parent.id if parent else 'null'),
        ))


def PageChooserPanel(field_name, page_type=None):
    return type('_PageChooserPanel', (BasePageChooserPanel,), {
        'field_name': field_name,
        'page_type': page_type,
    })


class BaseInlinePanel(EditHandler):
    @classmethod
    def get_panel_definitions(cls):
        # Look for a panels definition in the InlinePanel declaration
        if cls.panels is not None:
            return cls.panels
        # Failing that, get it from the model
        else:
            return extract_panel_definitions_from_model_class(cls.related.model, exclude=[cls.related.field.name])

    _child_edit_handler_class = None

    @classmethod
    def get_child_edit_handler_class(cls):
        if cls._child_edit_handler_class is None:
            panels = cls.get_panel_definitions()
            cls._child_edit_handler_class = MultiFieldPanel(panels, heading=cls.heading)

        return cls._child_edit_handler_class

    @classmethod
    def required_formsets(cls):
        return [cls.relation_name]

    @classmethod
    def widget_overrides(cls):
        overrides = cls.get_child_edit_handler_class().widget_overrides()
        if overrides:
            return {cls.relation_name: overrides}
        else:
            return {}

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

        empty_form = self.formset.empty_form
        empty_form.fields['DELETE'].widget = forms.HiddenInput()
        if self.formset.can_order:
            empty_form.fields['ORDER'].widget = forms.HiddenInput()

        self.empty_child = child_edit_handler_class(instance=empty_form.instance, form=empty_form)

    template = "wagtailadmin/edit_handlers/inline_panel.html"

    def render(self):
        return mark_safe(render_to_string(self.template, {
            'self': self,
            'can_order': self.formset.can_order,
        }))

    js_template = "wagtailadmin/edit_handlers/inline_panel.js"

    def render_js(self):
        return mark_safe(render_to_string(self.js_template, {
            'self': self,
            'can_order': self.formset.can_order,
        }))


def InlinePanel(base_model, relation_name, panels=None, label='', help_text=''):
    rel = getattr(base_model, relation_name).related
    return type('_InlinePanel', (BaseInlinePanel,), {
        'relation_name': relation_name,
        'related': rel,
        'panels': panels,
        'heading': label,
        'help_text': help_text,  # TODO: can we pick this out of the foreign key definition as an alternative? (with a bit of help from the inlineformset object, as we do for label/heading)
    })


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
    ], __('Common page configuration')),
]
