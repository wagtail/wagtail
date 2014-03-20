from django.db import models
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailadmin.edit_handlers import FieldPanel, InlinePanel

from modelcluster.fields import ParentalKey

FORM_FIELD_CHOICES = (
    ('SINGLELINE',   _('Single line text')),
    ('MULTILINE',    _('Multi-line text')),
    ('EMAIL',        _('Email')),
    ('NUMBER',       _('Number')),
    ('URL',          _('URL')),
    ('CHECKBOX',     _('Checkbox')),
    ('CHECKBOXES',   _('Checkboxes')),
    ('DROPDOWN',     _('Drop down')),
    ('RADIO',        _('Radio buttons')),
    ('DATE',         _('Date')),
    ('DATETIME',     _('Date/time')),
)
    
class AbstractFormFields(models.Model):
    #page = ParentalKey('wagtailforms.AbstractForm', related_name='form_fields')
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=16, choices = FORM_FIELD_CHOICES)
    required = models.BooleanField( default=True)
    choices = models.CharField(max_length=512, blank=True, help_text='Comma seperated list of choices')
    default_value = models.CharField(max_length=255, blank=True)
    help_text = models.CharField(max_length=255, blank=True)
    
    panels = [
        FieldPanel('label'),
        FieldPanel('field_type'),
        FieldPanel('required'),
        FieldPanel('choices'),
        FieldPanel('default_value'),
        FieldPanel('help_text'),
    ]
    
    class Meta:
        abstract = True 

 
    
class AbstractForm(Page):
    is_abstract = True #Don't display me in "Add"
    
    class Meta:
        abstract = True   
        
    def serve(self, request):
        # Get fields
        form_fields = self.form_fields

        return render(request, self.template, {
            'self': self,
        })
        
        
class ConcreteFormFields(Orderable, AbstractFormFields):
    page = ParentalKey('wagtailforms.ConcreteForm', related_name='form_fields')


class ConcreteForm(AbstractForm):    
    pass
    
ConcreteForm.content_panels = [
    FieldPanel('title', classname="full title"),
    InlinePanel(ConcreteForm, 'form_fields', label="Form Fields"),
]
