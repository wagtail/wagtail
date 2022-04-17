import datetime
import os

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import validate_email
from django.db import models
from django.template.response import TemplateResponse
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _

from wagtail.admin.mail import send_mail
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.forms.utils import get_field_clean_name
from wagtail.models import Orderable, Page

from .forms import FormBuilder, WagtailAdminFormPageForm

FORM_FIELD_CHOICES = (
    ("singleline", _("Single line text")),
    ("multiline", _("Multi-line text")),
    ("email", _("Email")),
    ("number", _("Number")),
    ("url", _("URL")),
    ("checkbox", _("Checkbox")),
    ("checkboxes", _("Checkboxes")),
    ("dropdown", _("Drop down")),
    ("multiselect", _("Multiple select")),
    ("radio", _("Radio buttons")),
    ("date", _("Date")),
    ("datetime", _("Date/time")),
    ("hidden", _("Hidden field")),
)


class AbstractFormSubmission(models.Model):
    """
    Data for a form submission.

    You can create custom submission model based on this abstract model.
    For example, if you need to save additional data or a reference to a user.
    """

    form_data = models.JSONField(encoder=DjangoJSONEncoder)
    page = models.ForeignKey(Page, on_delete=models.CASCADE)

    submit_time = models.DateTimeField(verbose_name=_("submit time"), auto_now_add=True)

    def get_data(self):
        """
        Returns dict with form data.

        You can override this method to add additional data.
        """

        return {
            **self.form_data,
            "submit_time": self.submit_time,
        }

    def __str__(self):
        return self.form_data

    class Meta:
        abstract = True
        verbose_name = _("form submission")
        verbose_name_plural = _("form submissions")


class FormSubmission(AbstractFormSubmission):
    """Data for a Form submission."""


class AbstractFormField(Orderable):
    """
    Database Fields required for building a Django Form field.
    """

    clean_name = models.CharField(
        verbose_name=_("name"),
        max_length=255,
        blank=True,
        default="",
        help_text=_(
            "Safe name of the form field, the label converted to ascii_snake_case"
        ),
    )
    label = models.CharField(
        verbose_name=_("label"),
        max_length=255,
        help_text=_("The label of the form field"),
    )
    field_type = models.CharField(
        verbose_name=_("field type"), max_length=16, choices=FORM_FIELD_CHOICES
    )
    required = models.BooleanField(verbose_name=_("required"), default=True)
    choices = models.TextField(
        verbose_name=_("choices"),
        blank=True,
        help_text=_(
            "Comma or new line separated list of choices. Only applicable in checkboxes, radio and dropdown."
        ),
    )
    default_value = models.TextField(
        verbose_name=_("default value"),
        blank=True,
        help_text=_(
            "Default value. Comma or new line separated values supported for checkboxes."
        ),
    )
    help_text = models.CharField(
        verbose_name=_("help text"), max_length=255, blank=True
    )

    panels = [
        FieldPanel("label"),
        FieldPanel("help_text"),
        FieldPanel("required"),
        FieldPanel("field_type", classname="formbuilder-type"),
        FieldPanel("choices", classname="formbuilder-choices"),
        FieldPanel("default_value", classname="formbuilder-default"),
    ]

    def save(self, *args, **kwargs):
        """
        When new fields are created, generate a template safe ascii name to use as the
        JSON storage reference for this field. Previously created fields will be updated
        to use the legacy unidecode method via checks & _migrate_legacy_clean_name.
        We do not want to update the clean name on any subsequent changes to the label
        as this would invalidate any previously submitted data.
        """

        is_new = self.pk is None
        if is_new:
            clean_name = get_field_clean_name(self.label)
            self.clean_name = clean_name

        super().save(*args, **kwargs)

    class Meta:
        abstract = True
        ordering = ["sort_order"]


class AbstractForm(Page):
    """
    A Form Page. Pages implementing a form should inherit from it
    """

    base_form_class = WagtailAdminFormPageForm

    form_builder = FormBuilder

    submissions_list_view_class = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self, "landing_page_template"):
            name, ext = os.path.splitext(self.template)
            self.landing_page_template = name + "_landing" + ext

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
            ("submit_time", _("Submission date")),
        ]
        data_fields += [
            (field.clean_name, field.label) for field in self.get_form_fields()
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

    def get_submissions_list_view_class(self):
        from .views import SubmissionsListView

        return self.submissions_list_view_class or SubmissionsListView

    def process_form_submission(self, form):
        """
        Accepts form instance with submitted data, user and page.
        Creates submission instance.

        You can override this method if you want to have custom creation logic.
        For example, if you want to save reference to a user.
        """

        return self.get_submission_class().objects.create(
            form_data=form.cleaned_data,
            page=self,
        )

    def render_landing_page(self, request, form_submission=None, *args, **kwargs):
        """
        Renders the landing page.

        You can override this method to return a different HttpResponse as
        landing page. E.g. you could return a redirect to a separate page.
        """
        context = self.get_context(request)
        context["form_submission"] = form_submission
        return TemplateResponse(
            request, self.get_landing_page_template(request), context
        )

    def serve_submissions_list_view(self, request, *args, **kwargs):
        """
        Returns list submissions view for admin.

        `list_submissions_view_class` can bse set to provide custom view class.
        Your class must be inherited from SubmissionsListView.
        """
        view = self.get_submissions_list_view_class().as_view()
        return view(request, form_page=self, *args, **kwargs)

    def serve(self, request, *args, **kwargs):
        if request.method == "POST":
            form = self.get_form(
                request.POST, request.FILES, page=self, user=request.user
            )

            if form.is_valid():
                form_submission = self.process_form_submission(form)
                return self.render_landing_page(
                    request, form_submission, *args, **kwargs
                )
        else:
            form = self.get_form(page=self, user=request.user)

        context = self.get_context(request)
        context["form"] = form
        return TemplateResponse(request, self.get_template(request), context)

    preview_modes = [
        ("form", _("Form")),
        ("landing", _("Landing page")),
    ]

    def serve_preview(self, request, mode_name):
        if mode_name == "landing":
            request.is_preview = True
            request.preview_mode = mode_name
            return self.render_landing_page(request)
        else:
            return super().serve_preview(request, mode_name)


def validate_to_address(value):
    for address in value.split(","):
        validate_email(address.strip())


class AbstractEmailForm(AbstractForm):
    """
    A Form Page that sends email. Pages implementing a form to be send to an email should inherit from it
    """

    to_address = models.CharField(
        verbose_name=_("to address"),
        max_length=255,
        blank=True,
        help_text=_(
            "Optional - form submissions will be emailed to these addresses. Separate multiple addresses by comma."
        ),
        validators=[validate_to_address],
    )
    from_address = models.EmailField(
        verbose_name=_("from address"), max_length=255, blank=True
    )
    subject = models.CharField(verbose_name=_("subject"), max_length=255, blank=True)

    def process_form_submission(self, form):
        submission = super().process_form_submission(form)
        if self.to_address:
            self.send_mail(form)
        return submission

    def send_mail(self, form):
        addresses = [x.strip() for x in self.to_address.split(",")]
        send_mail(
            self.subject,
            self.render_email(form),
            addresses,
            self.from_address,
        )

    def render_email(self, form):
        content = []

        cleaned_data = form.cleaned_data
        for field in form:
            if field.name not in cleaned_data:
                continue

            value = cleaned_data.get(field.name)

            if isinstance(value, list):
                value = ", ".join(value)

            # Format dates and datetimes with SHORT_DATE(TIME)_FORMAT
            if isinstance(value, datetime.datetime):
                value = date_format(value, settings.SHORT_DATETIME_FORMAT)
            elif isinstance(value, datetime.date):
                value = date_format(value, settings.SHORT_DATE_FORMAT)

            content.append("{}: {}".format(field.label, value))

        return "\n".join(content)

    class Meta:
        abstract = True
