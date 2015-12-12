from __future__ import unicode_literals

import json
import re

from unidecode import unidecode

from django.db import models
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.utils.encoding import python_2_unicode_compatible
from django.utils.six import text_type
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.contenttypes.models import ContentType

from wagtail.wagtailcore.models import Page, Orderable, UserPagePermissionsProxy, get_page_models
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailadmin.utils import send_mail

from .forms import FormBuilder


FORM_FIELD_CHOICES = (
    ('singleline', _('Single line text')),
    ('multiline', _('Multi-line text')),
    ('email', _('Email')),
    ('number', _('Number')),
    ('url', _('URL')),
    ('checkbox', _('Checkbox')),
    ('checkboxes', _('Checkboxes')),
    ('dropdown', _('Drop down')),
    ('radio', _('Radio buttons')),
    ('date', _('Date')),
    ('datetime', _('Date/time')),
)


HTML_EXTENSION_RE = re.compile(r"(.*)\.html")


@python_2_unicode_compatible
class FormSubmission(models.Model):
    """Data for a Form submission."""

    form_data = models.TextField()
    page = models.ForeignKey(Page)

    submit_time = models.DateTimeField(verbose_name=_('submit time'), auto_now_add=True)

    def get_data(self):
        return json.loads(self.form_data)

    def __str__(self):
        return self.form_data

    class Meta:
        verbose_name = _('form submission')


class AbstractFormField(Orderable):
    """
    Database Fields required for building a Django Form field.
    """

    label = models.CharField(
        verbose_name=_('label'),
        max_length=255,
        help_text=_('The label of the form field')
    )
    field_type = models.CharField(verbose_name=_('field type'), max_length=16, choices=FORM_FIELD_CHOICES)
    required = models.BooleanField(verbose_name=_('required'), default=True)
    choices = models.CharField(
        verbose_name=_('choices'),
        max_length=512,
        blank=True,
        help_text=_('Comma separated list of choices. Only applicable in checkboxes, radio and dropdown.')
    )
    default_value = models.CharField(
        verbose_name=_('default value'),
        max_length=255,
        blank=True,
        help_text=_('Default value. Comma separated values supported for checkboxes.')
    )
    help_text = models.CharField(verbose_name=_('help text'), max_length=255, blank=True)

    @property
    def clean_name(self):
        # unidecode will return an ascii string while slugify wants a
        # unicode string on the other hand, slugify returns a safe-string
        # which will be converted to a normal str
        return str(slugify(text_type(unidecode(self.label))))

    panels = [
        FieldPanel('label'),
        FieldPanel('help_text'),
        FieldPanel('required'),
        FieldPanel('field_type', classname="formbuilder-type"),
        FieldPanel('choices', classname="formbuilder-choices"),
        FieldPanel('default_value', classname="formbuilder-default"),
    ]

    class Meta:
        abstract = True
        ordering = ['sort_order']


_FORM_CONTENT_TYPES = None


def get_form_types():
    global _FORM_CONTENT_TYPES
    if _FORM_CONTENT_TYPES is None:
        form_models = [
            model for model in get_page_models()
            if issubclass(model, AbstractForm)
        ]

        _FORM_CONTENT_TYPES = list(
            ContentType.objects.get_for_models(*form_models).values()
        )
    return _FORM_CONTENT_TYPES


def get_forms_for_user(user):
    """
    Return a queryset of form pages that this user is allowed to access the submissions for
    """
    editable_pages = UserPagePermissionsProxy(user).editable_pages()
    return editable_pages.filter(content_type__in=get_form_types())


class AbstractForm(Page):
    """
    A Form Page. Pages implementing a form should inhert from it
    """

    form_builder = FormBuilder

    def __init__(self, *args, **kwargs):
        super(AbstractForm, self).__init__(*args, **kwargs)
        if not hasattr(self, 'landing_page_template'):
            template_wo_ext = re.match(HTML_EXTENSION_RE, self.template).group(1)
            self.landing_page_template = template_wo_ext + '_landing.html'

    class Meta:
        abstract = True

    def get_form_class(self):
        fb = self.form_builder(self.form_fields.all())
        return fb.get_form_class()

    def get_form_parameters(self):
        return {}

    def get_form(self, *args, **kwargs):
        form_class = self.get_form_class()
        form_params = self.get_form_parameters()
        form_params.update(kwargs)

        return form_class(*args, **form_params)

    def process_form_submission(self, form):
        FormSubmission.objects.create(
            form_data=json.dumps(form.cleaned_data, cls=DjangoJSONEncoder),
            page=self,
        )

    def serve(self, request):
        if request.method == 'POST':
            form = self.get_form(request.POST)

            if form.is_valid():
                self.process_form_submission(form)

                # render the landing_page
                # TODO: It is much better to redirect to it
                return render(
                    request,
                    self.landing_page_template,
                    self.get_context(request)
                )
        else:
            form = self.get_form()

        context = self.get_context(request)
        context['form'] = form
        return render(
            request,
            self.template,
            context
        )

    preview_modes = [
        ('form', 'Form'),
        ('landing', 'Landing page'),
    ]

    def serve_preview(self, request, mode):
        if mode == 'landing':
            return render(
                request,
                self.landing_page_template,
                self.get_context(request)
            )
        else:
            return super(AbstractForm, self).serve_preview(request, mode)


class AbstractEmailForm(AbstractForm):
    """
    A Form Page that sends email. Pages implementing a form to be send to an email should inherit from it
    """

    to_address = models.CharField(
        verbose_name=_('to address'), max_length=255, blank=True,
        help_text=_("Optional - form submissions will be emailed to this address")
    )
    from_address = models.CharField(verbose_name=_('from address'), max_length=255, blank=True)
    subject = models.CharField(verbose_name=_('subject'), max_length=255, blank=True)

    def process_form_submission(self, form):
        super(AbstractEmailForm, self).process_form_submission(form)

        if self.to_address:
            content = '\n'.join([x[1].label + ': ' + text_type(form.data.get(x[0])) for x in form.fields.items()])
            send_mail(self.subject, content, [self.to_address], self.from_address,)

    class Meta:
        abstract = True
