import functools
import re
from warnings import warn

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields import FieldDoesNotExist
from django.forms.formsets import DELETION_FIELD_NAME, ORDERING_FIELD_NAME
from django.forms.models import fields_for_model
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy
from taggit.managers import TaggableManager

from wagtail.admin import compare, widgets
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page
from wagtail.core.utils import camelcase_to_underscore, resolve_model_string
from wagtail.utils.decorators import cached_classmethod
from wagtail.utils.deprecation import RemovedInWagtail27Warning

# DIRECT_FORM_FIELD_OVERRIDES, FORM_FIELD_OVERRIDES are imported for backwards
# compatibility, as people are likely importing them from here and then
# appending their own overrides
from .forms.models import (  # NOQA
    DIRECT_FORM_FIELD_OVERRIDES, FORM_FIELD_OVERRIDES, WagtailAdminModelForm, formfield_for_dbfield)
from .forms.pages import WagtailAdminPageForm


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


class EditHandler:
    """
    Abstract class providing sensible default behaviours for objects implementing
    the EditHandler API
    """

    def __init__(self, heading='', classname='', help_text=''):
        self.heading = heading
        self.classname = classname
        self.help_text = help_text
        self.model = None
        self.instance = None
        self.request = None
        self.form = None

    def clone(self):
        return self.__class__(**self.clone_kwargs())

    def clone_kwargs(self):
        return {
            'heading': self.heading,
            'classname': self.classname,
            'help_text': self.help_text,
        }

    # return list of widget overrides that this EditHandler wants to be in place
    # on the form it receives
    def widget_overrides(self):
        return {}

    # return list of fields that this EditHandler expects to find on the form
    def required_fields(self):
        return []

    # return a dict of formsets that this EditHandler requires to be present
    # as children of the ClusterForm; the dict is a mapping from relation name
    # to parameters to be passed as part of get_form_for_model's 'formsets' kwarg
    def required_formsets(self):
        return {}

    # return any HTML that needs to be output on the edit page once per edit handler definition.
    # Typically this will be used to define snippets of HTML within <script type="text/x-template"></script> blocks
    # for Javascript code to work with.
    def html_declarations(self):
        return ''

    def bind_to(self, model=None, instance=None, request=None, form=None):
        if model is None and instance is not None and self.model is None:
            model = instance._meta.model

        new = self.clone()
        new.model = self.model if model is None else model
        new.instance = self.instance if instance is None else instance
        new.request = self.request if request is None else request
        new.form = self.form if form is None else form

        if new.model is not None:
            new.on_model_bound()

        if new.instance is not None:
            new.on_instance_bound()

        if new.request is not None:
            new.on_request_bound()

        if new.form is not None:
            new.on_form_bound()

        return new

    def bind_to_model(self, model):
        warn('EditHandler.bind_to_model(model) is deprecated. '
             'Use EditHandler.bind_to(model=model) instead',
             category=RemovedInWagtail27Warning)
        return self.bind_to(model=model)

    def bind_to_instance(self, instance, form, request):
        warn('EditHandler.bind_to_instance(instance, request, form) is deprecated. '
             'Use EditHandler.bind_to(instance=instance, request=request, form=form) instead',
             category=RemovedInWagtail27Warning)
        return self.bind_to(instance=instance, request=request, form=form)

    def on_model_bound(self):
        pass

    def on_instance_bound(self):
        pass

    def on_request_bound(self):
        pass

    def on_form_bound(self):
        pass

    def __repr__(self):
        return '<%s with model=%s instance=%s request=%s form=%s>' % (
            self.__class__.__name__,
            self.model, self.instance, self.request, self.form)

    def classes(self):
        """
        Additional CSS classnames to add to whatever kind of object this is at output.
        Subclasses of EditHandler should override this, invoking super().classes() to
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
            str(self.form[field_name])
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

    def get_comparison(self):
        return []


class BaseCompositeEditHandler(EditHandler):
    """
    Abstract class for EditHandlers that manage a set of sub-EditHandlers.
    Concrete subclasses must attach a 'children' property
    """

    def __init__(self, children=(), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.children = children

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        kwargs['children'] = self.children
        return kwargs

    def widget_overrides(self):
        # build a collated version of all its children's widget lists
        widgets = {}
        for handler_class in self.children:
            widgets.update(handler_class.widget_overrides())
        widget_overrides = widgets

        return widget_overrides

    def required_fields(self):
        fields = []
        for handler in self.children:
            fields.extend(handler.required_fields())
        return fields

    def required_formsets(self):
        formsets = {}
        for handler_class in self.children:
            formsets.update(handler_class.required_formsets())
        return formsets

    def html_declarations(self):
        return mark_safe(''.join([c.html_declarations() for c in self.children]))

    def on_model_bound(self):
        self.children = [child.bind_to(model=self.model)
                         for child in self.children]

    def on_instance_bound(self):
        self.children = [child.bind_to(instance=self.instance)
                         for child in self.children]

    def on_request_bound(self):
        self.children = [child.bind_to(request=self.request)
                         for child in self.children]

    def on_form_bound(self):
        children = []
        for child in self.children:
            if isinstance(child, FieldPanel):
                if self.form._meta.exclude:
                    if child.field_name in self.form._meta.exclude:
                        continue
                if self.form._meta.fields:
                    if child.field_name not in self.form._meta.fields:
                        continue
            children.append(child.bind_to(form=self.form))
        self.children = children

    def render(self):
        return mark_safe(render_to_string(self.template, {
            'self': self
        }))

    def get_comparison(self):
        comparators = []

        for child in self.children:
            comparators.extend(child.get_comparison())

        return comparators


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

    def get_form_class(self):
        """
        Construct a form class that has all the fields and formsets named in
        the children of this edit handler.
        """
        if self.model is None:
            raise AttributeError(
                '%s is not bound to a model yet. Use `.bind_to(model=model)` '
                'before using this method.' % self.__class__.__name__)
        # If a custom form class was passed to the EditHandler, use it.
        # Otherwise, use the base_form_class from the model.
        # If that is not defined, use WagtailAdminModelForm.
        model_form_class = getattr(self.model, 'base_form_class',
                                   WagtailAdminModelForm)
        base_form_class = self.base_form_class or model_form_class

        return get_form_for_model(
            self.model,
            form_class=base_form_class,
            fields=self.required_fields(),
            formsets=self.required_formsets(),
            widgets=self.widget_overrides())


class TabbedInterface(BaseFormEditHandler):
    template = "wagtailadmin/edit_handlers/tabbed_interface.html"

    def __init__(self, *args, **kwargs):
        self.base_form_class = kwargs.pop('base_form_class', None)
        super().__init__(*args, **kwargs)

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        kwargs['base_form_class'] = self.base_form_class
        return kwargs


class ObjectList(TabbedInterface):
    template = "wagtailadmin/edit_handlers/object_list.html"


class FieldRowPanel(BaseCompositeEditHandler):
    template = "wagtailadmin/edit_handlers/field_row_panel.html"

    def on_instance_bound(self):
        super().on_instance_bound()

        col_count = ' col%s' % (12 // len(self.children))
        # If child panel doesn't have a col# class then append default based on
        # number of columns
        for child in self.children:
            if not re.search(r'\bcol\d+\b', child.classname):
                child.classname += col_count


class MultiFieldPanel(BaseCompositeEditHandler):
    template = "wagtailadmin/edit_handlers/multi_field_panel.html"

    def classes(self):
        classes = super().classes()
        classes.append("multi-field")
        return classes


class HelpPanel(EditHandler):
    def __init__(self, content='', template='wagtailadmin/edit_handlers/help_panel.html',
                 heading='', classname=''):
        super().__init__(heading=heading, classname=classname)
        self.content = content
        self.template = template

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        del kwargs['help_text']
        kwargs.update(
            content=self.content,
            template=self.template,
        )
        return kwargs

    def render(self):
        return mark_safe(render_to_string(self.template, {
            'self': self
        }))


class FieldPanel(EditHandler):
    TEMPLATE_VAR = 'field_panel'

    def __init__(self, field_name, *args, **kwargs):
        widget = kwargs.pop('widget', None)
        if widget is not None:
            self.widget = widget
        super().__init__(*args, **kwargs)
        self.field_name = field_name

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        kwargs.update(
            field_name=self.field_name,
            widget=self.widget if hasattr(self, 'widget') else None,
        )
        return kwargs

    def widget_overrides(self):
        """check if a specific widget has been defined for this field"""
        if hasattr(self, 'widget'):
            return {self.field_name: self.widget}
        return {}

    def classes(self):
        classes = super().classes()

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
        return mark_safe(render_to_string(self.field_template, {
            'field': self.bound_field,
            'field_type': self.field_type(),
        }))

    def required_fields(self):
        return [self.field_name]

    def get_comparison_class(self):
        # Hide fields with hidden widget
        widget_override = self.widget_overrides().get(self.field_name, None)
        if widget_override and widget_override.is_hidden:
            return

        try:
            field = self.db_field

            if field.choices:
                return compare.ChoiceFieldComparison

            if field.is_relation:
                if isinstance(field, TaggableManager):
                    return compare.TagsFieldComparison
                elif field.many_to_many:
                    return compare.M2MFieldComparison

                return compare.ForeignObjectComparison

            if isinstance(field, RichTextField):
                return compare.RichTextFieldComparison
        except FieldDoesNotExist:
            pass

        return compare.FieldComparison

    def get_comparison(self):
        comparator_class = self.get_comparison_class()

        if comparator_class:
            try:
                return [functools.partial(comparator_class, self.db_field)]
            except FieldDoesNotExist:
                return []
        return []

    @cached_property
    def db_field(self):
        try:
            model = self.model
        except AttributeError:
            raise ImproperlyConfigured("%r must be bound to a model before calling db_field" % self)

        return model._meta.get_field(self.field_name)

    def on_form_bound(self):
        self.bound_field = self.form[self.field_name]
        self.heading = self.bound_field.label
        self.help_text = self.bound_field.help_text

    def __repr__(self):
        return "<%s '%s' with model=%s instance=%s request=%s form=%s>" % (
            self.__class__.__name__, self.field_name,
            self.model, self.instance, self.request, self.form)


class RichTextFieldPanel(FieldPanel):
    def get_comparison_class(self):
        return compare.RichTextFieldComparison


class BaseChooserPanel(FieldPanel):
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
        related_model = field.remote_field.model
        try:
            return getattr(self.instance, self.field_name)
        except related_model.DoesNotExist:
            # if the ForeignKey is null=False, Django decides to raise
            # a DoesNotExist exception here, rather than returning None
            # like every other unpopulated field type. Yay consistency!
            return

    def render_as_field(self):
        instance_obj = self.get_chosen_item()
        context = {
            'field': self.bound_field,
            self.object_type_name: instance_obj,
            'is_chosen': bool(instance_obj),  # DEPRECATED - passed to templates for backwards compatibility only
        }
        return mark_safe(render_to_string(self.field_template, context))


class PageChooserPanel(BaseChooserPanel):
    object_type_name = "page"

    def __init__(self, field_name, page_type=None, can_choose_root=False):
        super().__init__(field_name=field_name)

        if page_type:
            # Convert single string/model into list
            if not isinstance(page_type, (list, tuple)):
                page_type = [page_type]
        else:
            page_type = []

        self.page_type = page_type
        self.can_choose_root = can_choose_root

    def clone_kwargs(self):
        return {
            'field_name': self.field_name,
            'page_type': self.page_type,
            'can_choose_root': self.can_choose_root,
        }

    def widget_overrides(self):
        return {self.field_name: widgets.AdminPageChooser(
            target_models=self.target_models(),
            can_choose_root=self.can_choose_root)}

    def target_models(self):
        if self.page_type:
            target_models = []

            for page_type in self.page_type:
                try:
                    target_models.append(resolve_model_string(page_type))
                except LookupError:
                    raise ImproperlyConfigured(
                        "{0}.page_type must be of the form 'app_label.model_name', given {1!r}".format(
                            self.__class__.__name__, page_type
                        )
                    )
                except ValueError:
                    raise ImproperlyConfigured(
                        "{0}.page_type refers to model {1!r} that has not been installed".format(
                            self.__class__.__name__, page_type
                        )
                    )

            return target_models
        return [self.db_field.remote_field.model]


class InlinePanel(EditHandler):
    def __init__(self, relation_name, panels=None, heading='', label='',
                 min_num=None, max_num=None, *args, **kwargs):
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

    def get_panel_definitions(self):
        # Look for a panels definition in the InlinePanel declaration
        if self.panels is not None:
            return self.panels
        # Failing that, get it from the model
        return extract_panel_definitions_from_model_class(
            self.db_field.related_model,
            exclude=[self.db_field.field.name]
        )

    def get_child_edit_handler(self):
        panels = self.get_panel_definitions()
        child_edit_handler = MultiFieldPanel(panels, heading=self.heading)
        return child_edit_handler.bind_to(model=self.db_field.related_model)

    def required_formsets(self):
        child_edit_handler = self.get_child_edit_handler()
        return {
            self.relation_name: {
                'fields': child_edit_handler.required_fields(),
                'widgets': child_edit_handler.widget_overrides(),
                'min_num': self.min_num,
                'validate_min': self.min_num is not None,
                'max_num': self.max_num,
                'validate_max': self.max_num is not None
            }
        }

    def html_declarations(self):
        return self.get_child_edit_handler().html_declarations()

    def get_comparison(self):
        field_comparisons = []

        for panel in self.get_panel_definitions():
            field_comparisons.extend(
                panel.bind_to(model=self.db_field.related_model)
                .get_comparison())

        return [functools.partial(compare.ChildRelationComparison, self.db_field, field_comparisons)]

    def on_model_bound(self):
        manager = getattr(self.model, self.relation_name)
        self.db_field = manager.rel

    def on_form_bound(self):
        self.formset = self.form.formsets[self.relation_name]

        self.children = []
        for subform in self.formset.forms:
            # override the DELETE field to have a hidden input
            subform.fields[DELETION_FIELD_NAME].widget = forms.HiddenInput()

            # ditto for the ORDER field, if present
            if self.formset.can_order:
                subform.fields[ORDERING_FIELD_NAME].widget = forms.HiddenInput()

            child_edit_handler = self.get_child_edit_handler()
            self.children.append(child_edit_handler.bind_to(
                instance=subform.instance, request=self.request, form=subform))

        # if this formset is valid, it may have been re-ordered; respect that
        # in case the parent form errored and we need to re-render
        if self.formset.can_order and self.formset.is_valid():
            self.children.sort(
                key=lambda child: child.form.cleaned_data[ORDERING_FIELD_NAME] or 1)

        empty_form = self.formset.empty_form
        empty_form.fields[DELETION_FIELD_NAME].widget = forms.HiddenInput()
        if self.formset.can_order:
            empty_form.fields[ORDERING_FIELD_NAME].widget = forms.HiddenInput()

        self.empty_child = self.get_child_edit_handler()
        self.empty_child = self.empty_child.bind_to(
            instance=empty_form.instance, request=self.request, form=empty_form)

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


# This allows users to include the publishing panel in their own per-model override
# without having to write these fields out by hand, potentially losing 'classname'
# and therefore the associated styling of the publishing panel
class PublishingPanel(MultiFieldPanel):
    def __init__(self, **kwargs):
        updated_kwargs = {
            'children': [
                FieldRowPanel([
                    FieldPanel('go_live_at'),
                    FieldPanel('expire_at'),
                ], classname="label-above"),
            ],
            'heading': ugettext_lazy('Scheduled publishing'),
            'classname': 'publishing',
        }
        updated_kwargs.update(kwargs)
        super().__init__(**updated_kwargs)


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
        edit_handler = cls.edit_handler
    else:
        # construct a TabbedInterface made up of content_panels, promote_panels
        # and settings_panels, skipping any which are empty
        tabs = []

        if cls.content_panels:
            tabs.append(ObjectList(cls.content_panels,
                                   heading=ugettext_lazy('Content')))
        if cls.promote_panels:
            tabs.append(ObjectList(cls.promote_panels,
                                   heading=ugettext_lazy('Promote')))
        if cls.settings_panels:
            tabs.append(ObjectList(cls.settings_panels,
                                   heading=ugettext_lazy('Settings'),
                                   classname='settings'))

        edit_handler = TabbedInterface(tabs, base_form_class=cls.base_form_class)

    return edit_handler.bind_to(model=cls)


Page.get_edit_handler = get_edit_handler


class StreamFieldPanel(FieldPanel):
    def classes(self):
        classes = super().classes()
        classes.append("stream-field")

        # In case of a validation error, BlockWidget will take care of outputting the error on the
        # relevant sub-block, so we don't want the stream block as a whole to be wrapped in an 'error' class.
        if 'error' in classes:
            classes.remove("error")

        return classes

    def html_declarations(self):
        return self.block_def.all_html_declarations()

    def get_comparison_class(self):
        return compare.StreamFieldComparison

    def id_for_label(self):
        # a StreamField may consist of many input fields, so it's not meaningful to
        # attach the label to any specific one
        return ""

    def on_model_bound(self):
        super().on_model_bound()
        self.block_def = self.db_field.stream_block
