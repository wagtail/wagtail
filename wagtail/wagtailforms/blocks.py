from __future__ import unicode_literals

import django.forms
from django.utils.six import text_type, with_metaclass
from django.utils.text import slugify
from unidecode import unidecode

from wagtail.wagtailcore.blocks import BooleanBlock, CharBlock, ChoiceBlock, DeclarativeSubBlocksMetaclass, ListBlock, StructBlock
from .utils import FORM_FIELD_CHOICES


class AbstractField(object):
    '''
    A replacement class for wagtail.wagrailforms.models.AbstractFormField since
    we are not storing fields in the same way.
    '''
    label = ''
    field_type = None
    required = False
    choices = None
    default_value = None
    help_text = None

    def __init__(self, **kwargs):
        for key in kwargs:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

    @property
    def clean_name(self):
        # unidecode will return an ascii string while slugify wants a
        # unicode string on the other hand, slugify returns a safe-string
        # which will be converted to a normal str
        return str(slugify(text_type(unidecode(self.label))))


class FormFieldBlockMixin(with_metaclass(DeclarativeSubBlocksMetaclass, object)):
    label = CharBlock()
    required = BooleanBlock(default=False, required=False)
    help_text = CharBlock(required=False)
    
    def get_field_options(self, field):
        options = {}
        options['label'] = field['label']
        options['help_text'] = field['help_text']
        options['required'] = field['required']
        return options
    
    def create_field(self, field):
        options = self.get_field_options(field)
        return django.forms.CharField(**options)
    
    def clean_name(self, value):
        '''Converts the label for this form field to a key used as the form element name.
        
        value - StructValue - holds the stored information about the block.
        '''
        # unidecode will return an ascii string while slugify wants a
        # unicode string on the other hand, slugify returns a safe-string
        # which will be converted to a normal str
        return str(slugify(text_type(unidecode(value['label']))))


class FormFieldBlock(StructBlock):
    '''
    A block that defines a form field.
    '''
    field_type = ChoiceBlock(choices=FORM_FIELD_CHOICES)
    label = CharBlock()
    required = BooleanBlock(default=False, required=False)
    help_text = CharBlock(required=False)
    choices = CharBlock(required=False)
    default_value = CharBlock(required=False)
    
    def clean_name(self, value):
        # unidecode will return an ascii string while slugify wants a
        # unicode string on the other hand, slugify returns a safe-string
        # which will be converted to a normal str
        return str(slugify(text_type(unidecode(value['label']))))


class SingleLineFormFieldBlock(StructBlock, FormFieldBlockMixin):
    default_value = CharBlock(required=False)
    
    def get_field_options(self, field):
        options = super(SingleLineFormFieldBlock, self).get_field_options(field)
        options['initial'] = field['default_value']
        options['max_length'] = 255
        return options


class MultiLineFormFieldBlock(StructBlock, FormFieldBlockMixin):
    default_value = CharBlock(required=False)
    
    def get_field_options(self, field):
        options = super(MultiLineFormFieldBlock, self).get_field_options(field)
        options['initial'] = field['default_value']
        return options
    
    def create_field(self, field):
        options = self.get_field_options(field)
        return django.forms.CharField(widget=django.forms.Textarea, **options)


class EmailFormFieldBlock(StructBlock, FormFieldBlockMixin):
    
    def create_field(self, field):
        options = self.get_field_options(field)
        return django.forms.EmailField(**options)


class NumberFormFieldBlock(StructBlock, FormFieldBlockMixin):
    
    def create_field(self, field):
        options = self.get_field_options(field)
        return django.forms.DecimalField(**options)


class UrlFormFieldBlock(StructBlock, FormFieldBlockMixin):
    
    def create_field(self, field):
        options = self.get_field_options(field)
        return django.forms.URLField(**options)


class CheckboxFormFieldBlock(StructBlock, FormFieldBlockMixin):
    default_checked = BooleanBlock(default=False, required=False)
    
    def get_field_options(self, field):
        options = super(CheckboxFormFieldBlock, self).get_field_options(field)
        options['initial'] = field['default_checked']
        return options
    
    def create_field(self, field):
        options = self.get_field_options(field)
        return django.forms.BooleanField(**options)


class FieldChoiceBlock(StructBlock):
    key = CharBlock(required=True)
    description = CharBlock(required=True)


class DropdownFormFieldBlock(StructBlock, FormFieldBlockMixin):
    choices = ListBlock(FieldChoiceBlock)
    allow_multiple_selections = BooleanBlock(default=False, required=False)
    
    def get_field_options(self, field):
        options = super(DropdownFormFieldBlock, self).get_field_options(field)
        options['choices'] = [(x['key'], x['description']) for x in field['choices']]
        return options
    
    def create_field(self, field):
        options = self.get_field_options(field)
        if field['allow_multiple_selections']:
            return django.forms.MultipleChoiceField(**options)
        else:
            return django.forms.ChoiceField(**options)


class RadioFormFieldBlock(StructBlock, FormFieldBlockMixin):
    choices = ListBlock(FieldChoiceBlock)
    
    def get_field_options(self, field):
        options = super(RadioFormFieldBlock, self).get_field_options(field)
        options['choices'] = [(x['key'], x['description']) for x in field['choices']]
        return options
    
    def create_field(self, field):
        options = self.get_field_options(field)
        return django.forms.ChoiceField(widget=django.forms.RadioSelect, **options)


class DateFormFieldBlock(StructBlock, FormFieldBlockMixin):
    
    def create_field(self, field):
        options = self.get_field_options(field)
        return django.forms.DateField(**options)


class DateTimeFormFieldBlock(StructBlock, FormFieldBlockMixin):
    
    def create_field(self, field):
        options = self.get_field_options(field)
        return django.forms.DateTimeField(**options)

