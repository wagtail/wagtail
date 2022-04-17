import copy

from django.core.exceptions import ImproperlyConfigured
from django.db import models
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


# Callback to allow us to override the default form fields provided for each model field.
def formfield_for_dbfield(db_field, **kwargs):
    overrides = registry.get(db_field)
    if overrides:
        kwargs = dict(copy.deepcopy(overrides), **kwargs)

    return db_field.formfield(**kwargs)


class WagtailAdminModelFormOptions(PermissionedFormOptionsMixin, ClusterFormOptions):
    # Container for the options set in the inner 'class Meta' of a model form, supporting
    # extensions for both ClusterForm ('formsets') and PermissionedForm ('field_permissions').
    pass


class WagtailAdminModelFormMetaclass(PermissionedFormMetaclass, ClusterFormMetaclass):
    options_class = WagtailAdminModelFormOptions

    # Override the behaviour of the regular ModelForm metaclass -
    # which handles the translation of model fields to form fields -
    # to use our own formfield_for_dbfield function to do that translation.
    # This is done by sneaking a formfield_callback property into the class
    # being defined (unless the class already provides a formfield_callback
    # of its own).

    # while we're at it, we'll also set extra_form_count to 0, as we're creating
    # extra forms in JS
    extra_form_count = 0

    def __new__(cls, name, bases, attrs):
        if "formfield_callback" not in attrs or attrs["formfield_callback"] is None:
            attrs["formfield_callback"] = formfield_for_dbfield

        new_class = super(WagtailAdminModelFormMetaclass, cls).__new__(
            cls, name, bases, attrs
        )
        return new_class

    @classmethod
    def child_form(cls):
        return WagtailAdminModelForm


class WagtailAdminModelForm(
    PermissionedForm, ClusterForm, metaclass=WagtailAdminModelFormMetaclass
):
    def __init__(self, *args, **kwargs):
        # keep hold of the `for_user` kwarg as well as passing it on to PermissionedForm
        self.for_user = kwargs.get("for_user")
        super().__init__(*args, **kwargs)


# Now, any model forms built off WagtailAdminModelForm instead of ModelForm should pick up
# the nice form fields defined in FORM_FIELD_OVERRIDES.
