from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

from unidecode import unidecode
import json
import re

from wagtail.wagtailcore.models import PageBase, Page, Orderable, UserPagePermissionsProxy
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailforms.backends.email import EmailFormProcessor

from .forms import FormBuilder


FORM_FIELD_CHOICES = (
    ('singleline',   _('Single line text')),
    ('multiline',    _('Multi-line text')),
    ('email',        _('Email')),
    ('number',       _('Number')),
    ('url',          _('URL')),
    ('checkbox',     _('Checkbox')),
    ('checkboxes',   _('Checkboxes')),
    ('dropdown',     _('Drop down')),
    ('radio',        _('Radio buttons')),
    ('date',         _('Date')),
    ('datetime',     _('Date/time')),
)


HTML_EXTENSION_RE = re.compile(r"(.*)\.html")


class FormSubmission(models.Model):
    """Data for a Form submission."""

    form_data = models.TextField()
    page = models.ForeignKey(Page)

    submit_time = models.DateTimeField(auto_now_add=True)

    def get_data(self):
        return json.loads(self.form_data)

    def __unicode__(self):
        return self.form_data


class AbstractFormField(Orderable):
    """Database Fields required for building a Django Form field."""

    label = models.CharField(
        max_length=255,
        help_text=_('The label of the form field')
    )
    field_type = models.CharField(max_length=16, choices=FORM_FIELD_CHOICES)
    required = models.BooleanField(default=True)
    choices = models.CharField(
        max_length=512,
        blank=True,
        help_text=_('Comma seperated list of choices. Only applicable in checkboxes, radio and dropdown.')
    )
    default_value = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Default value. Comma seperated values supported for checkboxes.')
    )
    help_text = models.CharField(max_length=255, blank=True)

    @property
    def clean_name(self):
        # unidecode will return an ascii string while slugify wants a
        # unicode string on the other hand, slugify returns a safe-string
        # which will be converted to a normal str
        return str(slugify(unicode(unidecode(self.label))))

    panels = [
        FieldPanel('label'),
        FieldPanel('field_type', classname="formbuilder-type"),
        FieldPanel('required'),
        FieldPanel('choices', classname="formbuilder-choices"),
        FieldPanel('default_value', classname="formbuilder-default"),
        FieldPanel('help_text'),
    ]

    class Meta:
        abstract = True
        ordering = ['sort_order']


FORM_MODEL_CLASSES = []
_FORM_CONTENT_TYPES = []


def get_form_types():
    global _FORM_CONTENT_TYPES
    if len(_FORM_CONTENT_TYPES) != len(FORM_MODEL_CLASSES):
        _FORM_CONTENT_TYPES = [
            ContentType.objects.get_for_model(cls) for cls in FORM_MODEL_CLASSES
        ]
    return _FORM_CONTENT_TYPES


def get_forms_for_user(user):
    """Return a queryset of form pages that this user is allowed to access the submissions for"""
    editable_pages = UserPagePermissionsProxy(user).editable_pages()
    return editable_pages.filter(content_type__in=get_form_types())


class FormBase(PageBase):
    """Metaclass for Forms"""
    def __init__(cls, name, bases, dct):
        super(FormBase, cls).__init__(name, bases, dct)

        if not cls.is_abstract:
            # register this type in the list of page content types
            FORM_MODEL_CLASSES.append(cls)
            # Check if form_processing_backend is ok
            if hasattr(cls, 'form_processing_backend'):
                cls.form_processing_backend.validate_usage(cls)


class AbstractForm(Page):
    """A Form Page. Pages implementing a form should inhert from it"""

    __metaclass__ = FormBase

    form_builder = FormBuilder
    is_abstract = True  # Don't display me in "Add"

    def __init__(self, *args, **kwargs):
        super(AbstractForm, self).__init__(*args, **kwargs)
        if not hasattr(self, 'landing_page_template'):
            template_wo_ext = re.match(HTML_EXTENSION_RE, self.template).group(1)
            self.landing_page_template = template_wo_ext + '_landing.html'

    class Meta:
        abstract = True

    def get_form_parameters(self):
        return {}

    def serve(self, request):
        fb = self.form_builder(self.form_fields.all())
        form_class = fb.get_form_class()
        form_params = self.get_form_parameters()

        if request.method == 'POST':
            self.form = form_class(request.POST, **form_params)

            if self.form.is_valid():
                # remove csrf_token from form.data
                form_data = dict(
                    i for i in self.form.data.items()
                    if i[0] != 'csrfmiddlewaretoken'
                )

                FormSubmission.objects.create(
                    form_data=json.dumps(form_data),
                    page=self,
                )

                # If we have a form_processing_backend call its process method
                if hasattr(self, 'form_processing_backend'):
                    form_processor = self.form_processing_backend()
                    form_processor.process(self, self.form)

                # render the landing_page
                # TODO: It is much better to redirect to it
                return render(request, self.landing_page_template, {
                    'self': self,
                })
        else:
            self.form = form_class(**form_params)

        return render(request, self.template, {
            'self': self,
            'form': self.form,
        })

    def get_page_modes(self):
        return [
            ('form', 'Form'),
            ('landing', 'Landing page'),
        ]

    def show_as_mode(self, mode):
        if mode == 'landing':
            return render(self.dummy_request(), self.landing_page_template, {
                'self': self,
            })
        else:
            return super(AbstractForm, self).show_as_mode(mode)


class AbstractEmailForm(AbstractForm):
    """A Form Page that sends email. Pages implementing a form to be send to an email should inherit from it"""
    is_abstract = True  # Don't display me in "Add"
    form_processing_backend = EmailFormProcessor

    to_address = models.CharField(max_length=255, blank=True, help_text=_("Optional - form submissions will be emailed to this address"))
    from_address = models.CharField(max_length=255, blank=True)
    subject = models.CharField(max_length=255, blank=True)

    class Meta:
        abstract = True
