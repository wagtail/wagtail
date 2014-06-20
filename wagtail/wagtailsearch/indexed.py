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
        content_type = (cls._meta.app_label + "_" + cls.__name__).lower()

        # Get parent content type
        parent = cls.indexed_get_parent()
        if parent:
            parent_content_type = parent.indexed_get_content_type()
            return parent_content_type + "_" + content_type
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
            return (cls._meta.app_label + "_" + cls.__name__).lower()

    @classmethod
    def indexed_get_indexed_fields(cls):
        # New way
        if hasattr(cls, 'search_fields'):
            return dict((field.get_attname(cls), field.to_dict(cls)) for field in cls.search_fields)

        # Old way
        # Get indexed fields for this class as dictionary
        indexed_fields = cls.indexed_fields
        if isinstance(indexed_fields, dict):
            # Make sure we have a copy to prevent us accidentally changing the configuration
            indexed_fields = indexed_fields.copy()
        else:
            # Convert to dict
            if isinstance(indexed_fields, tuple):
                indexed_fields = list(indexed_fields)
            if isinstance(indexed_fields, string_types):
                indexed_fields = [indexed_fields]
            if isinstance(indexed_fields, list):
                indexed_fields = dict((field, dict(type="string")) for field in indexed_fields)
            if not isinstance(indexed_fields, dict):
                raise ValueError()

        # Get indexed fields for parent class
        parent = cls.indexed_get_parent(require_model=False)
        if parent:
            # Add parent fields into this list
            parent_indexed_fields = parent.indexed_get_indexed_fields().copy()
            parent_indexed_fields.update(indexed_fields)
            indexed_fields = parent_indexed_fields
        return indexed_fields

    indexed_fields = ()


class BaseField(object):
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

    def to_dict(self, cls):
        dic = {
            'type': 'string'
        }

        if 'es_extra' in self.kwargs:
            for key, value in self.kwargs['es_extra'].items():
                dic[key] = value

        return dic


class SearchField(BaseField):
    def __init__(self, field_name, boost=None, partial_match=False, **kwargs):
        super(SearchField, self).__init__(field_name, **kwargs)
        self.boost = boost
        self.partial_match = partial_match

    def to_dict(self, cls):
        dic = super(SearchField, self).to_dict(cls)

        if self.boost and 'boost' not in dic:
            dic['boost'] = self.boost

        if self.partial_match and 'analyzer' not in dic:
            dic['analyzer'] = 'edgengram_analyzer'

        return dic


class FilterField(BaseField):
    def to_dict(self, cls):
        dic = super(FilterField, self).to_dict(cls)

        if 'index' not in dic:
            dic['index'] = 'not_analyzed'

        return dic
