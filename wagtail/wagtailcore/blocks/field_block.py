from __future__ import absolute_import, unicode_literals

import datetime

from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH
from django.template.loader import render_to_string
from django.utils.encoding import force_text
from django.utils.dateparse import parse_date, parse_time, parse_datetime
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from wagtail.wagtailcore.rich_text import expand_db_html

from .base import Block


class FieldBlock(Block):
    class Meta:
        default = None

    def render_form(self, value, prefix='', errors=None):
        widget = self.field.widget

        if self.label:
            label_html = format_html(
                """<label for={label_id}>{label}</label> """,
                label_id=widget.id_for_label(prefix), label=self.label
            )
        else:
            label_html = ''

        widget_attrs = {'id': prefix, 'placeholder': self.label}

        if hasattr(widget, 'render_with_errors'):
            widget_html = widget.render_with_errors(prefix, value, attrs=widget_attrs, errors=errors)
            widget_has_rendered_errors = True
        else:
            widget_html = widget.render(prefix, value, attrs=widget_attrs)
            widget_has_rendered_errors = False

        return render_to_string('wagtailadmin/block_forms/field.html', {
            'name': self.name,
            'label': self.label,
            'classes': self.meta.classname,
            'widget': widget_html,
            'label_tag': label_html,
            'field': self.field,
            'errors': errors if (not widget_has_rendered_errors) else None
        })

    def value_from_datadict(self, data, files, prefix):
        return self.to_python(self.field.widget.value_from_datadict(data, files, prefix))

    def clean(self, value):
        return self.field.clean(value)


class CharBlock(FieldBlock):
    def __init__(self, required=True, help_text=None, max_length=None, min_length=None, **kwargs):
        # CharField's 'label' and 'initial' parameters are not exposed, as Block handles that functionality natively (via 'label' and 'default')
        self.field = forms.CharField(required=required, help_text=help_text, max_length=max_length, min_length=min_length)
        super(CharBlock, self).__init__(**kwargs)

    def get_searchable_content(self, value):
        return [force_text(value)]


class URLBlock(FieldBlock):
    def __init__(self, required=True, help_text=None, max_length=None, min_length=None, **kwargs):
        self.field = forms.URLField(required=required, help_text=help_text, max_length=max_length, min_length=min_length)
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
        # (to match Django's own behaviour for modelfields: https://github.com/django/django/blob/1.7.5/django/db/models/fields/__init__.py#L732-744)
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



class RichTextBlock(FieldBlock):
    @cached_property
    def field(self):
        from wagtail.wagtailcore.fields import RichTextArea
        return forms.CharField(widget=RichTextArea)

    def render_basic(self, value):
        return mark_safe('<div class="rich-text">' + expand_db_html(value) + '</div>')

    def get_searchable_content(self, value):
        return [force_text(value)]


class RawHTMLBlock(FieldBlock):
    def __init__(self, required=True, help_text=None, max_length=None, min_length=None, **kwargs):
        self.field = forms.CharField(
            required=required, help_text=help_text, max_length=max_length, min_length=min_length,
            widget = forms.Textarea)
        super(RawHTMLBlock, self).__init__(**kwargs)

    def render_basic(self, value):
        return mark_safe(value)  # if it isn't safe, that's the site admin's problem for allowing raw HTML blocks in the first place...

    class Meta:
        icon = 'code'


class ChooserBlock(FieldBlock):
    def __init__(self, required=True, **kwargs):
        self.required=required
        super(ChooserBlock, self).__init__(**kwargs)

    """Abstract superclass for fields that implement a chooser interface (page, image, snippet etc)"""
    @cached_property
    def field(self):
        return forms.ModelChoiceField(queryset=self.target_model.objects.all(), widget=self.widget, required=self.required)

    def to_python(self, value):
        if value is None or isinstance(value, self.target_model):
            return value
        else:
            try:
                return self.target_model.objects.get(pk=value)
            except self.target_model.DoesNotExist:
                return None

    def get_prep_value(self, value):
        if isinstance(value, self.target_model):
            return value.id
        else:
            return value

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
    @cached_property
    def target_model(self):
        from wagtail.wagtailcore.models import Page  # TODO: allow limiting to specific page types
        return Page

    @cached_property
    def widget(self):
        from wagtail.wagtailadmin.widgets import AdminPageChooser
        return AdminPageChooser

    def render_basic(self, value):
        if value:
            return format_html('<a href="{0}">{1}</a>', value.url, value.title)
        else:
            return ''


# Ensure that the blocks defined here get deconstructed as wagtailcore.blocks.FooBlock
# rather than wagtailcore.blocks.field.FooBlock
block_classes = [
    FieldBlock, CharBlock, URLBlock, RichTextBlock, RawHTMLBlock, ChooserBlock, PageChooserBlock,
    BooleanBlock, DateBlock, TimeBlock, DateTimeBlock, ChoiceBlock,
]
DECONSTRUCT_ALIASES = {
    cls: 'wagtail.wagtailcore.blocks.%s' % cls.__name__
    for cls in block_classes
}
__all__ = [cls.__name__ for cls in block_classes]
