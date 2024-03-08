from django import forms


class Options:
    """
    An object that serves as a container for configuration options. When a class is defined using
    OptionCollectingMetaclass as its metaclass, any attributes defined on an inner `class Meta`
    will be copied to an Options instance which will then be accessible as the class attribute
    `_meta`.

    The base Options class has no functionality of its own, but exists so that specific
    configuration options can be defined as mixins and collectively merged in to either Options or
    another base class with the same interface such as django.forms.models.ModelFormOptions,
    to arrive at a final class that recognises the desired set of options.
    """
    def __init__(self, options=None):
        pass


class OptionCollectingMetaclass(type):
    """
    Metaclass that handles inner `class Meta` definitions. When a class using
    OptionCollectingMetaclass defines an inner Meta class and an `options_class` attribute
    specifying an Options class, an Options object will be created from it and set as the class
    attribute `_meta`.
    """
    options_class = None

    def __new__(mcs, name, bases, attrs):
        new_class = super().__new__(mcs, name, bases, attrs)
        if mcs.options_class:
            new_class._meta = mcs.options_class(getattr(new_class, 'Meta', None))
        return new_class


class PermissionedFormOptionsMixin:
    """Handles the field_permissions option for PermissionedForm"""
    def __init__(self, options=None):
        super().__init__(options)
        self.field_permissions = getattr(options, 'field_permissions', None)


class PermissionedFormOptions(PermissionedFormOptionsMixin, Options):
    """Options class for PermissionedForm"""


FormMetaclass = type(forms.Form)

class PermissionedFormMetaclass(OptionCollectingMetaclass, FormMetaclass):
    """
    Extends the django.forms.Form metaclass with support for an inner `class Meta` that accepts
    a `field_permissions` configuration option
    """
    options_class = PermissionedFormOptions


class PermissionedForm(forms.Form, metaclass=PermissionedFormMetaclass):
    """
    An extension to `django.forms.Form` to accept an optional `for_user` keyword argument
    indicating the user the form will be presented to.
    
    Any fields named in the `field_permissions` dict in Meta will apply a permission test on the
    named permission using `User.has_perm`; if the user lacks that permission, the field will be
    omitted from the form.
    """
    def __init__(self, *args, for_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if for_user:
            field_perms = self._meta.field_permissions or {}
            for field_name, perm in field_perms.items():
                if not for_user.has_perm(perm):
                    del self.fields[field_name]


class PermissionedModelFormOptions(PermissionedFormOptionsMixin, forms.models.ModelFormOptions):
    """
    Options class for PermissionedModelForm; extends ModelForm's options to accept
    `field_permissions`
    """


class PermissionedModelFormMetaclass(PermissionedFormMetaclass, forms.models.ModelFormMetaclass):
    """
    Metaclass for PermissionedModelForm; extends the ModelForm metaclass to use
    PermissionedModelFormOptions in place of ModelFormOptions and thus accept the
    `field_permissions` option.

    Note that because ModelForm does not participate in the OptionCollectingMetaclass logic, this
    has the slightly hacky effect of letting ModelFormMetaclass construct a ModelFormOptions object
    for the lifetime of ModelFormMetaclass.__new__, which we promptly throw out and recreate as a
    PermissionedModelFormOptions object.
    """
    options_class = PermissionedModelFormOptions


class PermissionedModelForm(PermissionedForm, forms.ModelForm, metaclass=PermissionedModelFormMetaclass):
    """A ModelForm that implements the `for_user` keyword argument from PermissionedForm"""
