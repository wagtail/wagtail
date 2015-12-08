from __future__ import absolute_import, unicode_literals

import datetime

from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH
from django.template.loader import render_to_string
from django.utils import six
from django.utils.encoding import force_text
from django.utils.dateparse import parse_date, parse_time, parse_datetime
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from wagtail.wagtailcore.rich_text import RichText

from .base import Block


class FieldBlock(Block):
    """A block that wraps a Django form field"""
    class Meta:
        default = None

    def id_for_label(self, prefix):
        return self.field.widget.id_for_label(prefix)

    def render_form(self, value, prefix='', errors=None):
        widget = self.field.widget

        widget_attrs = {'id': prefix, 'placeholder': self.label}

        field_value = self.value_for_form(value)

        if hasattr(widget, 'render_with_errors'):
            widget_html = widget.render_with_errors(prefix, field_value, attrs=widget_attrs, errors=errors)
            widget_has_rendered_errors = True
        else:
            widget_html = widget.render(prefix, field_value, attrs=widget_attrs)
            widget_has_rendered_errors = False

        return render_to_string('wagtailadmin/block_forms/field.html', {
            'name': self.name,
            'classes': self.meta.classname,
            'widget': widget_html,
            'field': self.field,
            'errors': errors if (not widget_has_rendered_errors) else None
        })

    def value_from_form(self, value):
        """
        The value that we get back from the form field might not be the type
        that this block works with natively; for example, the block may want to
        wrap a simple value such as a string in an object that provides a fancy
        HTML rendering (e.g. EmbedBlock).

        We therefore provide this method to perform any necessary conversion
        from the form field value to the block's native value. As standard,
        this returns the form field value unchanged.
        """
        return value

    def value_for_form(self, value):
        """
        Reverse of value_from_form; convert a value of this block's native value type
        to one that can be rendered by the form field
        """
        return value

    def value_from_datadict(self, data, files, prefix):
        return self.value_from_form(self.field.widget.value_from_datadict(data, files, prefix))

    def clean(self, value):
        # We need an annoying value_for_form -> value_from_form round trip here to account for
        # the possibility that the form field is set up to validate a different value type to
        # the one this block works with natively
        return self.value_from_form(self.field.clean(self.value_for_form(value)))


class CharBlock(FieldBlock):
    def __init__(self, required=True, help_text=None, max_length=None, min_length=None, **kwargs):
        # CharField's 'label' and 'initial' parameters are not exposed, as Block handles that functionality natively
        # (via 'label' and 'default')
        self.field = forms.CharField(
            required=required,
            help_text=help_text,
            max_length=max_length,
            min_length=min_length
        )
        super(CharBlock, self).__init__(**kwargs)

    def get_searchable_content(self, value):
        return [force_text(value)]


class TextBlock(FieldBlock):
    def __init__(self, required=True, help_text=None, rows=1, max_length=None, min_length=None, **kwargs):
        self.field_options = {
            'required': required,
            'help_text': help_text,
            'max_length': max_length,
            'min_length': min_length
        }
        self.rows = rows
        super(TextBlock, self).__init__(**kwargs)

    @cached_property
    def field(self):
        from wagtail.wagtailadmin.widgets import AdminAutoHeightTextInput
        field_kwargs = {'widget': AdminAutoHeightTextInput(attrs={'rows': self.rows})}
        field_kwargs.update(self.field_options)
        return forms.CharField(**field_kwargs)

    def get_searchable_content(self, value):
        return [force_text(value)]


class URLBlock(FieldBlock):
    def __init__(self, required=True, help_text=None, max_length=None, min_length=None, **kwargs):
        self.field = forms.URLField(
            required=required,
            help_text=help_text,
            max_length=max_length,
            min_length=min_length
        )
        super(URLBlock, self).__init__(**kwargs)


class BooleanBlock(FieldBlock):
    def __init__(self, required=True, help_text=None, **kwargs):
        # NOTE: As with forms.BooleanField, the default of required=True means that the checkbox
        # must be ticked to pass validation (i.e. it's equivalent to an "I agree to the terms and
        # conditions" box). To get the conventional yes/no behaviour, you must explicitly pass
        # required=False.
        self.field = forms.BooleanField(required=required, help_text=help_text)
        super(BooleanBlock, self).__init__(**kwargs)


class DateBlock(FieldBlock):
    def __init__(self, required=True, help_text=None, **kwargs):
        self.field_options = {'required': required, 'help_text': help_text}
        super(DateBlock, self).__init__(**kwargs)

    @cached_property
    def field(self):
        from wagtail.wagtailadmin.widgets import AdminDateInput
        field_kwargs = {'widget': AdminDateInput}
        field_kwargs.update(self.field_options)
        return forms.DateField(**field_kwargs)

    def to_python(self, value):
        # Serialising to JSON uses DjangoJSONEncoder, which converts date/time objects to strings.
        # The reverse does not happen on decoding, because there's no way to know which strings
        # should be decoded; we have to convert strings back to dates here instead.
        if value is None or isinstance(value, datetime.date):
            return value
        else:
            return parse_date(value)


class TimeBlock(FieldBlock):
    def __init__(self, required=True, help_text=None, **kwargs):
        self.field_options = {'required': required, 'help_text': help_text}
        super(TimeBlock, self).__init__(**kwargs)

    @cached_property
    def field(self):
        from wagtail.wagtailadmin.widgets import AdminTimeInput
        field_kwargs = {'widget': AdminTimeInput}
        field_kwargs.update(self.field_options)
        return forms.TimeField(**field_kwargs)

    def to_python(self, value):
        if value is None or isinstance(value, datetime.time):
            return value
        else:
            return parse_time(value)


class DateTimeBlock(FieldBlock):
    def __init__(self, required=True, help_text=None, **kwargs):
        self.field_options = {'required': required, 'help_text': help_text}
        super(DateTimeBlock, self).__init__(**kwargs)

    @cached_property
    def field(self):
        from wagtail.wagtailadmin.widgets import AdminDateTimeInput
        field_kwargs = {'widget': AdminDateTimeInput}
        field_kwargs.update(self.field_options)
        return forms.DateTimeField(**field_kwargs)

    def to_python(self, value):
        if value is None or isinstance(value, datetime.datetime):
            return value
        else:
            return parse_datetime(value)


class ChoiceBlock(FieldBlock):
    choices = ()

    def __init__(self, choices=None, required=True, help_text=None, **kwargs):
        if choices is None:
            # no choices specified, so pick up the choice list defined at the class level
            choices = list(self.choices)
        else:
            choices = list(choices)

        # keep a copy of all kwargs (including our normalised choices list) for deconstruct()
        self._constructor_kwargs = kwargs.copy()
        self._constructor_kwargs['choices'] = choices
        if required is not True:
            self._constructor_kwargs['required'] = required
        if help_text is not None:
            self._constructor_kwargs['help_text'] = help_text

        # If choices does not already contain a blank option, insert one
        # (to match Django's own behaviour for modelfields:
        # https://github.com/django/django/blob/1.7.5/django/db/models/fields/__init__.py#L732-744)
        has_blank_choice = False
        for v1, v2 in choices:
            if isinstance(v2, (list, tuple)):
                # this is a named group, and v2 is the value list
                has_blank_choice = any([value in ('', None) for value, label in v2])
                if has_blank_choice:
                    break
            else:
                # this is an individual choice; v1 is the value
                if v1 in ('', None):
                    has_blank_choice = True
                    break

        if not has_blank_choice:
            choices = BLANK_CHOICE_DASH + choices

        self.field = forms.ChoiceField(choices=choices, required=required, help_text=help_text)
        super(ChoiceBlock, self).__init__(**kwargs)

    def deconstruct(self):
        """
        Always deconstruct ChoiceBlock instances as if they were plain ChoiceBlocks with their
        choice list passed in the constructor, even if they are actually subclasses. This allows
        users to define subclasses of ChoiceBlock in their models.py, with specific choice lists
        passed in, without references to those classes ending up frozen into migrations.
        """
        return ('wagtail.wagtailcore.blocks.ChoiceBlock', [], self._constructor_kwargs)

    def get_searchable_content(self, value):
        # Return the display value as the searchable value
        text_value = force_text(value)
        for k, v in self.field.choices:
            if isinstance(v, (list, tuple)):
                # This is an optgroup, so look inside the group for options
                for k2, v2 in v:
                    if value == k2 or text_value == force_text(k2):
                        return [k, v2]
            else:
                if value == k or text_value == force_text(k):
                    return [v]
        return []  # Value was not found in the list of choices


class RichTextBlock(FieldBlock):

    def __init__(self, required=True, help_text=None, **kwargs):
        self.field_options = {'required': required, 'help_text': help_text}
        super(RichTextBlock, self).__init__(**kwargs)

    def get_default(self):
        if isinstance(self.meta.default, RichText):
            return self.meta.default
        else:
            return RichText(self.meta.default)

    def to_python(self, value):
        # convert a source-HTML string from the JSONish representation
        # to a RichText object
        return RichText(value)

    def get_prep_value(self, value):
        # convert a RichText object back to a source-HTML string to go into
        # the JSONish representation
        return value.source

    @cached_property
    def field(self):
        from wagtail.wagtailcore.fields import RichTextArea
        return forms.CharField(widget=RichTextArea, **self.field_options)

    def value_for_form(self, value):
        # RichTextArea takes the source-HTML string as input (and takes care
        # of expanding it for the purposes of the editor)
        return value.source

    def value_from_form(self, value):
        # RichTextArea returns a source-HTML string; concert to a RichText object
        return RichText(value)

    def get_searchable_content(self, value):
        return [force_text(value.source)]


class RawHTMLBlock(FieldBlock):
    def __init__(self, required=True, help_text=None, max_length=None, min_length=None, **kwargs):
        self.field = forms.CharField(
            required=required, help_text=help_text, max_length=max_length, min_length=min_length,
            widget=forms.Textarea)
        super(RawHTMLBlock, self).__init__(**kwargs)

    def get_default(self):
        return mark_safe(self.meta.default or '')

    def to_python(self, value):
        return mark_safe(value)

    def get_prep_value(self, value):
        # explicitly convert to a plain string, just in case we're using some serialisation method
        # that doesn't cope with SafeText values correctly
        return six.text_type(value)

    def value_for_form(self, value):
        # need to explicitly mark as unsafe, or it'll output unescaped HTML in the textarea
        return six.text_type(value)

    def value_from_form(self, value):
        return mark_safe(value)

    class Meta:
        icon = 'code'


class ChooserBlock(FieldBlock):
    def __init__(self, required=True, help_text=None, **kwargs):
        self.required = required
        self.help_text = help_text
        super(ChooserBlock, self).__init__(**kwargs)

    """Abstract superclass for fields that implement a chooser interface (page, image, snippet etc)"""
    @cached_property
    def field(self):
        return forms.ModelChoiceField(
            queryset=self.target_model.objects.all(), widget=self.widget, required=self.required,
            help_text=self.help_text)

    def to_python(self, value):
        # the incoming serialised value should be None or an ID
        if value is None:
            return value
        else:
            try:
                return self.target_model.objects.get(pk=value)
            except self.target_model.DoesNotExist:
                return None

    def get_prep_value(self, value):
        # the native value (a model instance or None) should serialise to an ID or None
        if value is None:
            return None
        else:
            return value.id

    def value_from_form(self, value):
        # ModelChoiceField sometimes returns an ID, and sometimes an instance; we want the instance
        if value is None or isinstance(value, self.target_model):
            return value
        else:
            try:
                return self.target_model.objects.get(pk=value)
            except self.target_model.DoesNotExist:
                return None

    def clean(self, value):
        # ChooserBlock works natively with model instances as its 'value' type (because that's what you
        # want to work with when doing front-end templating), but ModelChoiceField.clean expects an ID
        # as the input value (and returns a model instance as the result). We don't want to bypass
        # ModelChoiceField.clean entirely (it might be doing relevant validation, such as checking page
        # type) so we convert our instance back to an ID here. It means we have a wasted round-trip to
        # the database when ModelChoiceField.clean promptly does its own lookup, but there's no easy way
        # around that...
        if isinstance(value, self.target_model):
            value = value.pk
        return super(ChooserBlock, self).clean(value)


class PageChooserBlock(ChooserBlock):
    def __init__(self, can_choose_root=False, **kwargs):
        self.can_choose_root = can_choose_root
        super(PageChooserBlock, self).__init__(**kwargs)

    @cached_property
    def target_model(self):
        from wagtail.wagtailcore.models import Page  # TODO: allow limiting to specific page types
        return Page

    @cached_property
    def widget(self):
        from wagtail.wagtailadmin.widgets import AdminPageChooser
        return AdminPageChooser(can_choose_root=self.can_choose_root)

    def render_basic(self, value):
        if value:
            return format_html('<a href="{0}">{1}</a>', value.url, value.title)
        else:
            return ''


# Ensure that the blocks defined here get deconstructed as wagtailcore.blocks.FooBlock
# rather than wagtailcore.blocks.field.FooBlock
block_classes = [
    FieldBlock, CharBlock, URLBlock, RichTextBlock, RawHTMLBlock, ChooserBlock, PageChooserBlock,
    TextBlock, BooleanBlock, DateBlock, TimeBlock, DateTimeBlock, ChoiceBlock,
]
DECONSTRUCT_ALIASES = {
    cls: 'wagtail.wagtailcore.blocks.%s' % cls.__name__
    for cls in block_classes
}
__all__ = [cls.__name__ for cls in block_classes]
