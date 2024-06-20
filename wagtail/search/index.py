import inspect
import logging

from django.apps import apps
from django.core import checks
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.fields.related import ForeignObjectRel, OneToOneRel, RelatedField
from modelcluster.fields import ParentalManyToManyField

from wagtail.search.backends import get_search_backends_with_name
from wagtail import __version__

logger = logging.getLogger("wagtail.search.index")


class Indexed:
    @classmethod
    def indexed_get_parent(cls, require_model=True):
        for base in cls.__bases__:
            if issubclass(base, Indexed) and (
                issubclass(base, models.Model) or require_model is False
            ):
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
    def get_search_fields(cls):
        search_fields = {}

        for field in cls.search_fields:
            search_fields[(type(field), field.field_name)] = field

        return list(search_fields.values())

    @classmethod
    def get_searchable_search_fields(cls):
        return [
            field for field in cls.get_search_fields() if isinstance(field, SearchField)
        ]

    @classmethod
    def get_autocomplete_search_fields(cls):
        return [
            field
            for field in cls.get_search_fields()
            if isinstance(field, AutocompleteField)
        ]

    @classmethod
    def get_filterable_search_fields(cls):
        return [
            field for field in cls.get_search_fields() if isinstance(field, FilterField)
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

    @classmethod
    def _has_field(cls, name):
        try:
            cls._meta.get_field(name)
            return True
        except FieldDoesNotExist:
            return hasattr(cls, name)

    @classmethod
    def check(cls, **kwargs):
        errors = super().check(**kwargs)
        errors.extend(cls._check_search_fields(**kwargs))
        return errors

    @classmethod
    def _check_search_fields(cls, **kwargs):
        errors = []
        for field in cls.get_search_fields():
            message = "{model}.search_fields contains non-existent field '{name}'"
            if not cls._has_field(field.field_name):
                errors.append(
                    checks.Warning(
                        message.format(model=cls.__name__, name=field.field_name),
                        obj=cls,
                        id="wagtailsearch.W004",
                    )
                )
        return errors

    search_fields = []


def get_indexed_models():
    return [
        model
        for model in apps.get_models()
        if issubclass(model, Indexed)
        and not model._meta.abstract
        and model.search_fields
    ]


def class_is_indexed(cls):
    return (
        issubclass(cls, Indexed)
        and issubclass(cls, models.Model)
        and not cls._meta.abstract
        and cls.search_fields
    )


def get_indexed_instance(instance, check_exists=True):
    indexed_instance = instance.get_indexed_instance()
    if indexed_instance is None:
        return

    # Make sure that the instance is in its class's indexed objects
    if (
        check_exists
        and not type(indexed_instance)
        .get_indexed_objects()
        .filter(pk=indexed_instance.pk)
        .exists()
    ):
        return

    return indexed_instance


def insert_or_update_object(instance):
    indexed_instance = get_indexed_instance(instance)

    if indexed_instance:
        for backend_name, backend in get_search_backends_with_name(
            with_auto_update=True
        ):
            try:
                backend.add(indexed_instance)
            except Exception:
                # Log all errors
                logger.exception(
                    "Exception raised while adding %r into the '%s' search backend",
                    indexed_instance,
                    backend_name,
                )

                # Catch exceptions for backends that use an external service like Elasticsearch
                # This is to prevent data loss if that external service was to go down and the user's
                # save request was to fail.
                # But note that we don't want this for database backends though as an error during a
                # database transaction will require the transaction to be rolled back anyway. So If
                # we caught the error here, the request will only crash again when the next database
                # query is made but then the error message wouldn't be very informative.
                if not backend.catch_indexing_errors:
                    raise


def remove_object(instance):
    indexed_instance = get_indexed_instance(instance, check_exists=False)

    if indexed_instance:
        for backend_name, backend in get_search_backends_with_name(
            with_auto_update=True
        ):
            try:
                backend.delete(indexed_instance)
            except Exception:
                # Log all errors
                logger.exception(
                    "Exception raised while deleting %r from the '%s' search backend",
                    indexed_instance,
                    backend_name,
                )

                # Only catch the exception if the backend requires this
                # See the comments in insert_or_update_object for an explanation
                if not backend.catch_indexing_errors:
                    raise


class BaseField:
    def __init__(self, field_name, **kwargs):
        self.field_name = field_name
        self.kwargs = kwargs

    def get_field(self, cls):
        return cls._meta.get_field(self.field_name)

    def get_attname(self, cls):
        try:
            field = self.get_field(cls)
            return field.attname
        except FieldDoesNotExist:
            return self.field_name

    def get_definition_model(self, cls):
        try:
            field = self.get_field(cls)
            return field.model
        except FieldDoesNotExist:
            # Find where it was defined by walking the inheritance tree
            for base_cls in inspect.getmro(cls):
                if self.field_name in base_cls.__dict__:
                    return base_cls

    def get_type(self, cls):
        if "type" in self.kwargs:
            return self.kwargs["type"]

        try:
            field = self.get_field(cls)

            # Follow foreign keys to find underlying type
            # We use a while loop as it's possible for a foreign key
            # to target a foreign key in another model.
            # (for example, a foreign key to a child page model will
            # point to the `page_ptr_id` field so we need to follow this
            # second foreign key to find the `id`` field in the Page model)
            while isinstance(field, RelatedField):
                field = field.target_field

            return field.get_internal_type()

        except FieldDoesNotExist:
            return "CharField"

    def get_value(self, obj):
        from taggit.managers import TaggableManager

        try:
            field = self.get_field(obj.__class__)
            value = field.value_from_object(obj)
            if hasattr(field, "get_searchable_content"):
                value = field.get_searchable_content(value)
                if __version__ < 6:
                    value = value.as_list()

            elif isinstance(field, TaggableManager):
                # As of django-taggit 1.0, value_from_object returns a list of Tag objects,
                # which matches what we want
                pass
            elif isinstance(field, RelatedField):
                # The type of the ForeignKey may have a get_searchable_content method that we should
                # call. Firstly we need to find the field its referencing but it may be referencing
                # another RelatedField (eg an FK to page_ptr_id) so we need to run this in a while
                # loop to find the actual remote field.
                remote_field = field
                while isinstance(remote_field, RelatedField):
                    remote_field = remote_field.target_field

                if hasattr(remote_field, "get_searchable_content"):
                    value = remote_field.get_searchable_content(value)
            return value
        except FieldDoesNotExist:
            value = getattr(obj, self.field_name, None)
            if hasattr(value, "__call__"):
                value = value()
            return value

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.field_name}>"


class SearchField(BaseField):
    def __init__(self, field_name, boost=None, **kwargs):
        super().__init__(field_name, **kwargs)
        self.boost = boost
        self.unique_boosts = kwargs.pop("unique_boosts", [boost])


class AutocompleteField(BaseField):
    pass


class FilterField(BaseField):
    pass


class RelatedFields:
    def __init__(self, field_name, fields):
        self.field_name = field_name
        self.fields = fields

    def get_field(self, cls):
        return cls._meta.get_field(self.field_name)

    def get_definition_model(self, cls):
        field = self.get_field(cls)
        return field.model

    def get_value(self, obj):
        field = self.get_field(obj.__class__)

        if isinstance(field, (RelatedField, ForeignObjectRel)):
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

        if isinstance(field, RelatedField) and not isinstance(
            field, ParentalManyToManyField
        ):
            if field.many_to_one or field.one_to_one:
                queryset = queryset.select_related(self.field_name)
            elif field.one_to_many or field.many_to_many:
                queryset = queryset.prefetch_related(self.field_name)

        elif isinstance(field, ForeignObjectRel):
            # Reverse relation
            if isinstance(field, OneToOneRel):
                # select_related for reverse OneToOneField
                queryset = queryset.select_related(self.field_name)
            else:
                # prefetch_related for anything else (reverse ForeignKey/ManyToManyField)
                queryset = queryset.prefetch_related(self.field_name)

        return queryset


# '''
# Implementation of the `SearchableContent` class

# - `add_content`: Adds content with a specified boost value.
# - `merge_content`: Merges the content of another `SearchableContent` object.
# - `multiply_boosts`: Multiplies all boost values by a given multiplier.
# - `get_unique_boosts`: Gets the set of unique boost values.
# - `as_dict`: Returns the content as a dictionary.

# We will use this class for `get_searchable_content` in the `StreamBlock` or other relevant blocks.
# '''
class SearchableContent:
    def __init__(self, data=None):
        # Initialize with an empty dictionary or provided data
        self.data = data or {}

    def add_content(self, boost, content):
        """
        Add content to the SearchableContent object with the specified boost value.
        """
        if boost not in self.data:
            self.data[boost] = []

        self.data[boost].append(content)

    def merge_content(self, other):
        """
        Merge the content of another SearchableContent object into this object.
        """
        for boost, content_list in other.data.items():
            if boost not in self.data:
                self.data[boost] = []
            self.data[boost].extend(content_list)

    def multiply_boosts(self, multiplier):
        """
        Multiply all boost values in the SearchableContent object by the given multiplier.
        """
        for boost in list(self.data.keys()):
            new_boost = boost * multiplier
            self.data[new_boost] = self.data.pop(boost)

    def get_unique_boosts(self):
        """
        Get the set of unique boost values present in the SearchableContent object.
        """
        return set(self.data.keys())

    def as_dict(self):
        """
        Get the content as a dictionary.
        """
        return self.data.copy()

    def as_list(self):
        """
        Get a single list containing all content from different boost values.
        """
        combined_content = []
        for content_list in self.data.values():
            combined_content.extend(content_list)
        return combined_content

    def __str__(self):
        """
        Return a string representation of the SearchableContent object.
        """
        return f"SearchableContent(data={self.data})"

    def __eq__(self, other):
        """
        Compare two SearchableContent objects for equality.
        """
        return isinstance(other, SearchableContent) and self.data == other.data

    def __ne__(self, other):
        """
        Compare two SearchableContent objects for inequality.
        """
        return not self.__eq__(other)

    def __json__(self):
        """
        Convert the SearchableContent object to a JSON-serializable dictionary.
        """
        return {str(key): value for key, value in self.data.items()}
