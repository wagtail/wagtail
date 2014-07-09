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
    def indexed_get_indexed_fields(cls):
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
                indexed_fields = dict((field, dict(type='string')) for field in indexed_fields)
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

    @classmethod
    def get_search_fields(cls):
        search_fields = []

        if hasattr(cls, 'search_fields'):
            search_fields.extend(cls.search_fields)

        # Backwards compatibility with old indexed_fields setting

        # Get indexed fields
        indexed_fields = cls.indexed_get_indexed_fields()

        # Display deprecation warning if indexed_fields has been used
        if indexed_fields:
            warnings.warn("'indexed_fields' setting is now deprecated."
                          "Use 'search_fields' instead.", DeprecationWarning)

        # Convert them into search fields
        for field_name, _config in indexed_fields.items():
            # Copy the config to prevent is trashing anything accidentally
            config = _config.copy()

            # Check if this is a filter field
            if config.get('index', None) == 'not_analyzed':
                config.pop('index')
                search_fields.append(FilterField(field_name, es_extra=config))
                continue

            # Must be a search field, check for boosting and partial matching
            boost = config.pop('boost', None)

            partial_match = False
            if config.get('analyzer', None) == 'edgengram_analyzer':
                partial_match = True
                config.pop('analyzer')

            # Add the field
            search_fields.append(SearchField(field_name, boost=boost, partial_match=partial_match, es_extra=config))

        # Remove any duplicate entries into search fields
        # We need to take into account that fields can be indexed as both a SearchField and as a FilterField
        search_fields_dict = {}
        for field in search_fields:
            search_fields_dict[(field.field_name, type(field))] = field
        search_fields = search_fields_dict.values()

        return search_fields

    @classmethod
    def get_searchable_search_fields(cls):
        return filter(lambda field: isinstance(field, SearchField), cls.get_search_fields())

    @classmethod
    def get_filterable_search_fields(cls):
        return filter(lambda field: isinstance(field, FilterField), cls.get_search_fields())

    indexed_fields = ()


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
