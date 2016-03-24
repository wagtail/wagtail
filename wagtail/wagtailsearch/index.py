from django.apps import apps
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db.models.fields.related import ForeignObjectRel, OneToOneRel, RelatedField

from wagtail.utils.deprecation import SearchFieldsShouldBeAList


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
        queryset = cls.objects.all()

        # Add prefetch/select related for RelatedFields
        for field in cls.get_search_fields():
            if isinstance(field, RelatedFields):
                queryset = field.select_on_queryset(queryset)

        return queryset

    def get_indexed_instance(self):
        """
        If the indexed model uses multi table inheritance, override this method
        to return the instance in its most specific class so it reindexes properly.
        """
        return self

    search_fields = SearchFieldsShouldBeAList([], name='search_fields on Indexed subclasses')


def get_indexed_models():
    return [
        model for model in apps.get_models()
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
        return cls._meta.get_field(self.field_name)

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
            value = field.value_from_object(obj)
            if hasattr(field, 'get_searchable_content'):
                value = field.get_searchable_content(value)
            return value
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


class RelatedFields(object):
    def __init__(self, field_name, fields):
        self.field_name = field_name
        self.fields = fields

    def get_index_name(self, cls):
        return self.field_name

    def get_field(self, cls):
        return cls._meta.get_field(self.field_name)

    def get_value(self, obj):
        field = self.get_field(obj.__class__)

        if isinstance(field, RelatedField):
            return getattr(obj, self.field_name)

    def select_on_queryset(self, queryset):
        """
        This method runs either prefetch_related or select_related on the queryset
        to improve indexing speed of the relation.

        It decides which method to call based on the number of related objects:
         - single (eg ForeignKey, OneToOne), it runs select_related
         - multiple (eg ManyToMany, reverse ForeignKey) it runs prefetch_related
        """
        try:
            field = self.get_field(queryset.model)
        except FieldDoesNotExist:
            return queryset

        if isinstance(field, RelatedField):
            if field.many_to_one or field.one_to_one:
                queryset = queryset.select_related(self.field_name)
            elif field.one_to_many or field.many_to_many:
                queryset = queryset.prefetch_related(self.field_name)

        elif isinstance(field, ForeignObjectRel):
            # Reverse relation
            # Note: we will never get here on Django 1.7 and below as get_field
            # does not return reverse relations
            if isinstance(field, OneToOneRel):
                # select_related for reverse OneToOneField
                queryset = queryset.select_related(self.field_name)
            else:
                # prefetch_related for anything else (reverse ForeignKey/ManyToManyField)
                queryset = queryset.prefetch_related(self.field_name)

        return queryset
