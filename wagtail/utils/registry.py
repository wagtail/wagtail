from django.core.exceptions import ImproperlyConfigured
from django.db import models


class ObjectTypeRegistry:
    """
    Implements a lookup table for mapping objects to values according to the object type.
    The most specific type according to the object's inheritance chain is selected.
    """

    def __init__(self):
        # values in this dict will be returned if the field type exactly matches an item here
        self.values_by_exact_class = {}

        # values in this dict will be returned if any class in the field's inheritance chain
        # matches, preferring more specific subclasses
        self.values_by_class = {}

    def register(self, cls, value=None, exact_class=False):
        if exact_class:
            self.values_by_exact_class[cls] = value
        else:
            self.values_by_class[cls] = value

    def get_by_type(self, cls):
        try:
            return self.values_by_exact_class[cls]
        except KeyError:
            for ancestor in cls.mro():
                try:
                    return self.values_by_class[ancestor]
                except KeyError:
                    pass

    def get(self, obj):
        value = self.get_by_type(obj.__class__)

        if callable(value) and not isinstance(value, type):
            value = value(obj)

        return value


class ModelFieldRegistry(ObjectTypeRegistry):
    """
    Handles the recurring pattern where we need to register different values for different
    model field types, and retrieve the one that most closely matches a given model field,
    according to its type (taking inheritance into account), and in the case of foreign keys,
    the type of the related model (again, taking inheritance into account).

    For example, this is used by wagtail.admin.forms.models when constructing model forms:
    we use such a registry to retrieve the appropriate dict of arguments to pass to the
    form field constructor. A lookup for a models.TextField will return a dict specifying a
    text area widget, and a lookup for a foreign key to Image will return a dict specifying
    an image chooser widget.
    """

    def __init__(self):
        super().__init__()
        self.values_by_class[models.ForeignKey] = self.foreign_key_lookup

        # values in this dict will be returned if the field is a foreign key to a related
        # model in here, matching most specific subclass first
        self.values_by_fk_related_model = {}

    def register(self, field_class, to=None, value=None, exact_class=False):
        if to:
            if field_class == models.ForeignKey:
                self.values_by_fk_related_model[to] = value
            else:
                raise ImproperlyConfigured(
                    "The 'to' argument on ModelFieldRegistry.register is only valid for ForeignKey fields"
                )
        else:
            super().register(field_class, value=value, exact_class=exact_class)

    def foreign_key_lookup(self, field):
        value = None
        target_model = field.remote_field.model

        for model in target_model.mro():
            if model in self.values_by_fk_related_model:
                value = self.values_by_fk_related_model[model]
                break

        if callable(value) and not isinstance(value, type):
            value = value(field)

        return value
