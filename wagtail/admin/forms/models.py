import copy

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from modelcluster.forms import ClusterForm, ClusterFormMetaclass
from taggit.managers import TaggableManager

from wagtail.admin import widgets
from wagtail.admin.forms.tags import TagField
from wagtail.core.models import Page

# Form field properties to override whenever we encounter a model field
# that matches one of these types - including subclasses


# Overrides that should take effect for foreign key fields to a given model
def _get_page_chooser_overrides(db_field):
    return {
        "widget": widgets.AdminPageChooser(target_models=[db_field.remote_field.model])
    }


FOREIGN_KEY_MODEL_OVERRIDES = {
    Page: _get_page_chooser_overrides,
}


def _get_foreign_key_overrides(db_field):
    target_model = db_field.remote_field.model
    for model in target_model.mro():
        if model in FOREIGN_KEY_MODEL_OVERRIDES:
            overrides = FOREIGN_KEY_MODEL_OVERRIDES[model]
            if callable(overrides):
                overrides = overrides(db_field)
            return overrides

    # no override found for the given model
    return {}


def _get_tag_field_overrides(db_field):
    return {"form_class": TagField, "tag_model": db_field.related_model}


FORM_FIELD_OVERRIDES = {
    models.ForeignKey: _get_foreign_key_overrides,
    models.DateField: {"widget": widgets.AdminDateInput},
    models.TimeField: {"widget": widgets.AdminTimeInput},
    models.DateTimeField: {"widget": widgets.AdminDateTimeInput},
    TaggableManager: _get_tag_field_overrides,
}

# Form field properties to override whenever we encounter a model field
# that matches one of these types exactly, ignoring subclasses.
# (This allows us to override the widget for models.TextField, but leave
# the RichTextField widget alone)
DIRECT_FORM_FIELD_OVERRIDES = {
    models.TextField: {"widget": widgets.AdminAutoHeightTextInput},
}


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

    if to:
        if db_field_class == models.ForeignKey:
            FOREIGN_KEY_MODEL_OVERRIDES[to] = override
        else:
            raise ImproperlyConfigured(
                "The 'to' argument on register_form_field_override is only valid for ForeignKey fields"
            )
    elif exact_class:
        DIRECT_FORM_FIELD_OVERRIDES[db_field_class] = override
    else:
        FORM_FIELD_OVERRIDES[db_field_class] = override


# Callback to allow us to override the default form fields provided for each model field.
def formfield_for_dbfield(db_field, **kwargs):
    # adapted from django/contrib/admin/options.py

    overrides = None

    # If we've got overrides for the formfield defined, use 'em. **kwargs
    # passed to formfield_for_dbfield override the defaults.
    if db_field.__class__ in DIRECT_FORM_FIELD_OVERRIDES:
        overrides = DIRECT_FORM_FIELD_OVERRIDES[db_field.__class__]
    else:
        for klass in db_field.__class__.mro():
            if klass in FORM_FIELD_OVERRIDES:
                overrides = FORM_FIELD_OVERRIDES[klass]
                break

    if overrides:
        if callable(overrides):
            overrides = overrides(db_field)

        kwargs = dict(copy.deepcopy(overrides), **kwargs)

    return db_field.formfield(**kwargs)


class WagtailAdminModelFormMetaclass(ClusterFormMetaclass):
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


class WagtailAdminModelForm(ClusterForm, metaclass=WagtailAdminModelFormMetaclass):
    pass


# Now, any model forms built off WagtailAdminModelForm instead of ModelForm should pick up
# the nice form fields defined in FORM_FIELD_OVERRIDES.
