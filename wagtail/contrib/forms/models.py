import json
import os

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.shortcuts import render
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from unidecode import unidecode

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.admin.utils import send_mail
from wagtail.core.models import Orderable, Page

from .forms import FormBuilder, WagtailAdminFormPageForm
from .views import SubmissionsListView

FORM_FIELD_CHOICES = (
    ('singleline', _('Single line text')),
    ('multiline', _('Multi-line text')),
    ('email', _('Email')),
    ('number', _('Number')),
    ('url', _('URL')),
    ('checkbox', _('Checkbox')),
    ('checkboxes', _('Checkboxes')),
    ('dropdown', _('Drop down')),
    ('multiselect', _('Multiple select')),
    ('radio', _('Radio buttons')),
    ('date', _('Date')),
    ('datetime', _('Date/time')),
    ('hidden', _('Hidden field')),
)


class AbstractFormSubmission(models.Model):
    """
    Data for a form submission.

    You can create custom submission model based on this abstract model.
    For example, if you need to save additional data or a reference to a user.
    """

    form_data = models.TextField()
    page = models.ForeignKey(Page, on_delete=models.CASCADE)

    submit_time = models.DateTimeField(verbose_name=_('submit time'), auto_now_add=True)

    def get_data(self):
        """
        Returns dict with form data.

        You can override this method to add additional data.
        """
        form_data = json.loads(self.form_data)
        form_data.update({
            'submit_time': self.submit_time,
        })

        return form_data

    def __str__(self):
        return self.form_data

    class Meta:
        abstract = True
        verbose_name = _('form submission')


class FormSubmission(AbstractFormSubmission):
    """Data for a Form submission."""


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
    choices = models.TextField(
        verbose_name=_('choices'),
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
        return str(slugify(str(unidecode(self.label))))

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


class AbstractForm(Page):
    """
    A Form Page. Pages implementing a form should inherit from it
    """

    base_form_class = WagtailAdminFormPageForm

    form_builder = FormBuilder

    submissions_list_view_class = SubmissionsListView

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self, 'landing_page_template'):
            name, ext = os.path.splitext(self.template)
            self.landing_page_template = name + '_landing' + ext

    class Meta:
        abstract = True

    def get_form_fields(self):
        """
        Form page expects `form_fields` to be declared.
        If you want to change backwards relation name,
        you need to override this method.
        """

        return self.form_fields.all()

    def get_data_fields(self):
        """
        Returns a list of tuples with (field_name, field_label).
        """

        data_fields = [
            ('submit_time', _('Submission date')),
        ]
        data_fields += [
            (field.clean_name, field.label)
            for field in self.get_form_fields()
        ]

        return data_fields

    def get_form_class(self):
        fb = self.form_builder(self.get_form_fields())
        return fb.get_form_class()

    def get_form_parameters(self):
        return {}

    def get_form(self, *args, **kwargs):
        form_class = self.get_form_class()
        form_params = self.get_form_parameters()
        form_params.update(kwargs)

        return form_class(*args, **form_params)

    def get_landing_page_template(self, request, *args, **kwargs):
        return self.landing_page_template

    def get_submission_class(self):
        """
        Returns submission class.

        You can override this method to provide custom submission class.
        Your class must be inherited from AbstractFormSubmission.
        """

        return FormSubmission

    def process_form_submission(self, form):
        """
        Accepts form instance with submitted data, user and page.
        Creates submission instance.

        You can override this method if you want to have custom creation logic.
        For example, if you want to save reference to a user.
        """

        return self.get_submission_class().objects.create(
            form_data=json.dumps(form.cleaned_data, cls=DjangoJSONEncoder),
            page=self,
        )

    def render_landing_page(self, request, form_submission=None, *args, **kwargs):
        """
        Renders the landing page.

        You can override this method to return a different HttpResponse as
        landing page. E.g. you could return a redirect to a separate page.
        """
        context = self.get_context(request)
        context['form_submission'] = form_submission
        return render(
            request,
            self.get_landing_page_template(request),
            context
        )

    def serve_submissions_list_view(self, request, *args, **kwargs):
        """
        Returns list submissions view for admin.

        `list_submissions_view_class` can bse set to provide custom view class.
        Your class must be inherited from SubmissionsListView.
        """
        view = self.submissions_list_view_class.as_view()
        return view(request, form_page=self, *args, **kwargs)

    def serve(self, request, *args, **kwargs):
        if request.method == 'POST':
            form = self.get_form(request.POST, request.FILES, page=self, user=request.user)

            if form.is_valid():
                form_submission = self.process_form_submission(form)
                return self.render_landing_page(request, form_submission, *args, **kwargs)
        else:
            form = self.get_form(page=self, user=request.user)

        context = self.get_context(request)
        context['form'] = form
        return render(
            request,
            self.get_template(request),
            context
        )

    preview_modes = [
        ('form', 'Form'),
        ('landing', 'Landing page'),
    ]

    def serve_preview(self, request, mode):
        if mode == 'landing':
            request.is_preview = True
            return self.render_landing_page(request)
        else:
            return super().serve_preview(request, mode)


class AbstractEmailForm(AbstractForm):
    """
    A Form Page that sends email. Pages implementing a form to be send to an email should inherit from it
    """

    to_address = models.CharField(
        verbose_name=_('to address'), max_length=255, blank=True,
        help_text=_("Optional - form submissions will be emailed to these addresses. Separate multiple addresses by comma.")
    )
    from_address = models.CharField(verbose_name=_('from address'), max_length=255, blank=True)
    subject = models.CharField(verbose_name=_('subject'), max_length=255, blank=True)

    def process_form_submission(self, form):
        submission = super().process_form_submission(form)
        if self.to_address:
            self.send_mail(form)
        return submission

    def send_mail(self, form):
        addresses = [x.strip() for x in self.to_address.split(',')]
        content = []
        for field in form:
            value = field.value()
            if isinstance(value, list):
                value = ', '.join(value)
            content.append('{}: {}'.format(field.label, value))
        content = '\n'.join(content)
        send_mail(self.subject, content, addresses, self.from_address,)

    class Meta:
        abstract = True
