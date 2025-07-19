import copy

from django import VERSION as DJANGO_VERSION
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _
from modelcluster.forms import ClusterForm, ClusterFormMetaclass, ClusterFormOptions
from permissionedforms import (
    PermissionedForm,
    PermissionedFormMetaclass,
    PermissionedFormOptionsMixin,
)
from taggit.managers import TaggableManager

from wagtail.admin import widgets
from wagtail.admin.forms.tags import TagField
from wagtail.models import Page
from wagtail.utils.registry import ModelFieldRegistry

# Define a registry of form field properties to override for a given model field
registry = ModelFieldRegistry()

# Aliases to lookups in the overrides registry, for backwards compatibility
FORM_FIELD_OVERRIDES = registry.values_by_class
DIRECT_FORM_FIELD_OVERRIDES = registry.values_by_exact_class


def register_form_field_override(
    db_field_class, to=None, override=None, exact_class=False
):
    """
    Define parameters for form fields to be used by WagtailAdminModelForm for a given
    database field.
    """

    if override is None:
        raise ImproperlyConfigured(
            "register_form_field_override must be passed an 'override' keyword argument"
        )

    if to and db_field_class != models.ForeignKey:
        raise ImproperlyConfigured(
            "The 'to' argument on register_form_field_override is only valid for ForeignKey fields"
        )

    registry.register(db_field_class, to=to, value=override, exact_class=exact_class)


# Define built-in overrides

# Date / time fields
register_form_field_override(
    models.DateField, override={"widget": widgets.AdminDateInput}
)
register_form_field_override(
    models.TimeField, override={"widget": widgets.AdminTimeInput}
)
register_form_field_override(
    models.DateTimeField, override={"widget": widgets.AdminDateTimeInput}
)

# Auto-height text fields (defined as exact_class=True so that it doesn't take effect for RichTextField)
register_form_field_override(
    models.TextField,
    override={"widget": widgets.AdminAutoHeightTextInput},
    exact_class=True,
)

# Page chooser
register_form_field_override(
    models.ForeignKey,
    to=Page,
    override=lambda db_field: {
        "widget": widgets.AdminPageChooser(target_models=[db_field.remote_field.model])
    },
)

# Tag fields
register_form_field_override(
    TaggableManager,
    override=(
        lambda db_field: {"form_class": TagField, "tag_model": db_field.related_model}
    ),
)

# Slug fields
register_form_field_override(
    models.SlugField,
    override={"widget": widgets.SlugInput},
)

# Remove the following block when the minimum Django version is >= 5.0.
if (5, 0) <= DJANGO_VERSION < (6, 0):
    register_form_field_override(
        models.URLField,
        override={"assume_scheme": "https"},
    )


# Callback to allow us to override the default form fields provided for each model field.
def formfield_for_dbfield(db_field, **kwargs):
    overrides = registry.get(db_field)
    if overrides:
        kwargs = dict(copy.deepcopy(overrides), **kwargs)

    return db_field.formfield(**kwargs)


class WagtailAdminModelFormOptions(PermissionedFormOptionsMixin, ClusterFormOptions):
    # Container for the options set in the inner 'class Meta' of a model form, supporting
    # extensions for both ClusterForm ('formsets') and PermissionedForm ('field_permissions').

    def __init__(self, options=None):
        super().__init__(options)
        self.defer_required_on_fields = getattr(options, "defer_required_on_fields", [])


class WagtailAdminModelFormMetaclass(PermissionedFormMetaclass, ClusterFormMetaclass):
    options_class = WagtailAdminModelFormOptions

    # set extra_form_count to 0, as we're creating extra forms in JS
    extra_form_count = 0

    @classmethod
    def child_form(cls):
        return WagtailAdminModelForm


class WagtailAdminModelForm(
    PermissionedForm, ClusterForm, metaclass=WagtailAdminModelFormMetaclass
):
    def __init__(self, *args, **kwargs):
        # keep hold of the `for_user` kwarg as well as passing it on to PermissionedForm
        self.for_user = kwargs.get("for_user")
        self.deferred_required_fields = []
        self.deferred_formset_min_nums = {}
        super().__init__(*args, **kwargs)

    def defer_required_fields(self):
        if self.deferred_required_fields or self.deferred_formset_min_nums:
            # defer_required_fields has already been called
            return

        for field_name in self._meta.defer_required_on_fields:
            try:
                if self.fields[field_name].required:
                    self.fields[field_name].required = False
                    self.deferred_required_fields.append(field_name)
            except KeyError:
                pass

        for name, formset in self.formsets.items():
            for form in formset:
                form.defer_required_fields()
            if formset.min_num is not None:
                self.deferred_formset_min_nums[name] = formset.min_num
                formset.min_num = 0

    def restore_required_fields(self):
        for name, formset in self.formsets.items():
            for form in formset:
                form.restore_required_fields()
            if name in self.deferred_formset_min_nums:
                formset.min_num = self.deferred_formset_min_nums[name]
        self.deferred_formset_min_nums = {}

        for field_name in self.deferred_required_fields:
            self.fields[field_name].required = True
        self.deferred_required_fields = []

    class Meta:
        formfield_callback = formfield_for_dbfield


# Now, any model forms built off WagtailAdminModelForm instead of ModelForm should pick up
# the nice form fields defined in FORM_FIELD_OVERRIDES.


class WagtailAdminDraftStateFormMixin:
    @property
    def show_schedule_publishing_toggle(self):
        return "go_live_at" in self.__class__.base_fields

    def clean(self):
        super().clean()

        # Check scheduled publishing fields
        go_live_at = self.cleaned_data.get("go_live_at")
        expire_at = self.cleaned_data.get("expire_at")

        # Go live must be before expire
        if go_live_at and expire_at:
            if go_live_at > expire_at:
                msg = _("Go live date/time must be before expiry date/time")
                self.add_error("go_live_at", forms.ValidationError(msg))
                self.add_error("expire_at", forms.ValidationError(msg))

        # Expire at must be in the future
        if expire_at and expire_at < timezone.now():
            self.add_error(
                "expire_at",
                forms.ValidationError(_("Expiry date/time must be in the future")),
            )

        # Don't allow an existing first_published_at to be unset by clearing the field
        if (
            "first_published_at" in self.cleaned_data
            and not self.cleaned_data["first_published_at"]
        ):
            del self.cleaned_data["first_published_at"]

        return self.cleaned_data
