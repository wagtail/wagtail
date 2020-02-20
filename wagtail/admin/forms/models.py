import copy

from django.db import models
from modelcluster.forms import ClusterForm, ClusterFormMetaclass
from taggit.managers import TaggableManager

from wagtail.admin import widgets
from wagtail.admin.forms.tags import TagField


# Form field properties to override whenever we encounter a model field
# that matches one of these types - including subclasses

def _get_tag_field_overrides(db_field):
    return {'form_class': TagField, 'tag_model': db_field.related_model}


FORM_FIELD_OVERRIDES = {
    models.DateField: {'widget': widgets.AdminDateInput},
    models.TimeField: {'widget': widgets.AdminTimeInput},
    models.DateTimeField: {'widget': widgets.AdminDateTimeInput},
    TaggableManager: _get_tag_field_overrides,
}

# Form field properties to override whenever we encounter a model field
# that matches one of these types exactly, ignoring subclasses.
# (This allows us to override the widget for models.TextField, but leave
# the RichTextField widget alone)
DIRECT_FORM_FIELD_OVERRIDES = {
    models.TextField: {'widget': widgets.AdminAutoHeightTextInput},
}


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
        if 'formfield_callback' not in attrs or attrs['formfield_callback'] is None:
            attrs['formfield_callback'] = formfield_for_dbfield

        new_class = super(WagtailAdminModelFormMetaclass, cls).__new__(cls, name, bases, attrs)
        return new_class

    @classmethod
    def child_form(cls):
        return WagtailAdminModelForm


class WagtailAdminModelForm(ClusterForm, metaclass=WagtailAdminModelFormMetaclass):
    @property
    def media(self):
        # Include media from formsets forms. This allow StreamField in InlinePanel for example.
        media = super().media
        for formset in self.formsets.values():
            media += formset.media
        return media


# Now, any model forms built off WagtailAdminModelForm instead of ModelForm should pick up
# the nice form fields defined in FORM_FIELD_OVERRIDES.
