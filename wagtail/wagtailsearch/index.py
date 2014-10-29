import warnings

from six import string_types

from django.db import models


class Indexed(object):
    @classmethod
    def indexed_get_parent(cls, require_model=True):
        for base in cls.__bases__:
            if issubclass(base, Indexed) and (issubclass(base, models.Model) or require_model is False):
                return base

    @classmethod
    def indexed_get_content_type(cls):
        # Work out content type
        content_type = (cls._meta.app_label + '_' + cls.__name__).lower()

        # Get parent content type
        parent = cls.indexed_get_parent()
        if parent:
            parent_content_type = parent.indexed_get_content_type()
            return parent_content_type + '_' + content_type
        else:
            return content_type

    @classmethod
    def indexed_get_toplevel_content_type(cls):
        # Get parent content type
        parent = cls.indexed_get_parent()
        if parent:
            return parent.indexed_get_content_type()
        else:
            # At toplevel, return this content type
            return (cls._meta.app_label + '_' + cls.__name__).lower()

    @classmethod
    def get_search_fields(cls):
        search_fields = {}

        for field in cls.search_fields:
            search_fields[(type(field), field.field_name)] = field

        return list(search_fields.values())

    @classmethod
    def get_searchable_search_fields(cls):
        return [
            field for field in cls.get_search_fields()
            if isinstance(field, SearchField)
        ]

    @classmethod
    def get_filterable_search_fields(cls):
        return [
            field for field in cls.get_search_fields()
            if isinstance(field, FilterField)
        ]

    @classmethod
    def get_indexed_objects(cls):
        return cls.objects.all()

    def get_indexed_instance(self):
        """
        If the indexed model uses multi table inheritance, override this method
        to return the instance in its most specific class so it reindexes properly.
        """
        return self

    search_fields = ()


def get_indexed_models():
    return [
        model for model in models.get_models()
        if issubclass(model, Indexed) and not model._meta.abstract
    ]


def class_is_indexed(cls):
    return issubclass(cls, Indexed) and issubclass(cls, models.Model) and not cls._meta.abstract


class BaseField(object):
    suffix = ''

    def __init__(self, field_name, **kwargs):
        self.field_name = field_name
        self.kwargs = kwargs

    def get_field(self, cls):
        return cls._meta.get_field_by_name(self.field_name)[0]

    def get_attname(self, cls):
        try:
            field = self.get_field(cls)
            return field.attname
        except models.fields.FieldDoesNotExist:
            return self.field_name

    def get_index_name(self, cls):
        return self.get_attname(cls) + self.suffix

    def get_type(self, cls):
        if 'type' in self.kwargs:
            return self.kwargs['type']

        try:
            field = self.get_field(cls)
            return field.get_internal_type()
        except models.fields.FieldDoesNotExist:
            return 'CharField'

    def get_value(self, obj):
        try:
            field = self.get_field(obj.__class__)
            return field._get_val_from_obj(obj)
        except models.fields.FieldDoesNotExist:
            value = getattr(obj, self.field_name, None)
            if hasattr(value, '__call__'):
                value = value()
            return value

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.field_name)


class SearchField(BaseField):
    def __init__(self, field_name, boost=None, partial_match=False, **kwargs):
        super(SearchField, self).__init__(field_name, **kwargs)
        self.boost = boost
        self.partial_match = partial_match


class FilterField(BaseField):
    suffix = '_filter'

