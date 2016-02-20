from __future__ import unicode_literals

from django import forms
from django.utils.six import text_type
from django.utils.text import slugify
from unidecode import unidecode

from wagtail.wagtailcore.blocks import BooleanBlock, CharBlock, ChoiceBlock, StructBlock
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


class FormFieldBlock(StructBlock):
    '''
    A block that defines a form field.
    '''
    label = CharBlock()
    field_type = ChoiceBlock(choices=FORM_FIELD_CHOICES)
    required = BooleanBlock(default=False, required=False)
    choices = CharBlock(required=False)
    default_value = CharBlock(required=False)
    help_text = CharBlock(required=False)
    
    def clean_name(self, value):
        # unidecode will return an ascii string while slugify wants a
        # unicode string on the other hand, slugify returns a safe-string
        # which will be converted to a normal str
        return str(slugify(text_type(unidecode(value['label']))))
