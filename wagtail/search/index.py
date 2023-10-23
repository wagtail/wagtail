import inspect
import logging
from typing import Optional
from warnings import warn

from django.apps import apps
from django.core import checks
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.fields.related import ForeignObjectRel, OneToOneRel, RelatedField
from modelcluster.fields import ParentalManyToManyField

from wagtail.search.backends import get_search_backends_with_name
from wagtail.utils.deprecation import RemovedInWagtail60Warning

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
    def _get_search_field(cls, field_dict, field, parent_field):
        if isinstance(field, IndexedField):
            generated_fields = field.generate_fields(parent_field)
            for generated_field in generated_fields:
                field_dict[
                    (type(generated_field), generated_field.field_name)
                ] = generated_field
        elif isinstance(field, RelatedFields):
            related_fields = {}
            for related_field in field.fields:
                related_fields |= cls._get_search_field(related_field, field)
            field_dict[(RelatedFields, field.field_name)] = RelatedFields(
                field.model_field_name, list(related_fields.values())
            )
        else:
            field_dict[(type(field), field.field_name, field.model_field_name)] = field
        return field_dict

    @classmethod
    def get_search_fields(cls, parent_field=None):
        search_fields = {}

        for field in cls.search_fields:
            search_fields |= cls._get_search_field(search_fields, field, parent_field)

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
            if not cls._has_field(field.field_name) and not cls._has_field(
                field.model_field_name
            ):
                errors.append(
                    checks.Warning(
                        message.format(model=cls.__name__, name=field.field_name),
                        obj=cls,
                        id="wagtailsearch.W004",
                    )
                )

        parent_fields = []
        for parent_cls in cls.__bases__:
            parent_fields += getattr(parent_cls, "search_fields", [])
        model_fields = []
        for field in cls.get_search_fields():
            model_field_name = getattr(field, "model_field_name", None)
            if not model_field_name:
                model_field_name = field.field_name
            if field not in parent_fields and model_field_name not in model_fields:
                message = "indexed field '{name}' is defined in {model} and {parent}"
                definition_model = field.get_definition_model(cls)
                if definition_model != cls:
                    errors.append(
                        checks.Warning(
                            message.format(
                                model=cls.__name__,
                                name=field.field_name,
                                parent=definition_model.__name__,
                            ),
                            obj=cls,
                            id="wagtailsearch.W005",
                        )
                    )
                    model_fields.append(model_field_name)
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
    def __init__(self, field_name, model_field_name=None, **kwargs):
        self.field_name = field_name
        self.model_field_name = model_field_name or field_name
        self.kwargs = kwargs

    def get_field(self, cls):
        if self.model_field_name:
            return cls._meta.get_field(self.model_field_name)
        return cls._meta.get_field(self.field_name)

    def get_attname(self, cls):
        if self.model_field_name and self.model_field_name != self.field_name:
            return self.field_name

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
            model_field_name = self.model_field_name
            if model_field_name:
                name_parts = model_field_name.split(".")
                if len(name_parts) > 1:
                    model_field_name = name_parts[0]

            # Find where it was defined by walking the inheritance tree
            for base_cls in inspect.getmro(cls):
                if (
                    self.field_name in base_cls.__dict__
                    or model_field_name in base_cls.__dict__
                ):
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
            if value is None:
                value = getattr(obj, self.model_field_name, None)
            if hasattr(value, "__call__"):
                value = value()
            return value

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.field_name}>"


class SearchField(BaseField):
    def __init__(self, field_name, boost=None, partial_match=False, **kwargs):
        super().__init__(field_name, **kwargs)
        if partial_match:
            warn(
                "The partial_match option on SearchField has no effect and will be removed. "
                "Use AutocompleteField instead",
                category=RemovedInWagtail60Warning,
            )
        self.boost = boost


class AutocompleteField(BaseField):
    pass


class FilterField(BaseField):
    pass


class RelatedFields:
    def __init__(self, field_name, fields, model_field_name=None):
        self.field_name = field_name
        self.model_field_name = model_field_name or field_name
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


class IndexedField(BaseField):
    def __init__(
        self,
        *args,
        boost: Optional[float] = None,
        search: bool = False,
        search_kwargs: Optional[dict] = None,
        autocomplete: bool = False,
        autocomplete_kwargs: Optional[dict] = None,
        filter: bool = False,
        filter_kwargs: Optional[dict] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.boost = self.kwargs["boost"] = boost
        self.search = self.kwargs["search"] = search
        self.search_kwargs = self.kwargs["search_kwargs"] = search_kwargs
        self.autocomplete = self.kwargs["autocomplete"] = autocomplete
        self.autocomplete_kwargs = self.kwargs[
            "autocomplete_kwargs"
        ] = autocomplete_kwargs
        self.filter = self.kwargs["filter"] = filter
        self.filter_kwargs = self.kwargs["filter_kwargs"] = filter_kwargs

    def generate_fields(self, parent_field: BaseField = None) -> list[BaseField]:
        generated_fields = []
        field_name = self.model_field_name
        if parent_field:
            field_name = f"{parent_field.model_field_name}.{field_name}"

        if self.search:
            generated_fields.append(self.generate_search_field(field_name))
        if self.autocomplete:
            generated_fields.append(self.generate_autocomplete_field(field_name))
        if self.filter:
            generated_fields.append(self.generate_filter_field(field_name))

    def generate_search_field(self, field_name: str) -> SearchField:
        return SearchField(
            field_name,
            model_field_name=self.model_field_name,
            **self.search_kwargs,
        )

    def generate_autocomplete_field(self, field_name: str) -> AutocompleteField:
        return AutocompleteField(
            field_name,
            model_field_name=self.model_field_name,
            **self.autocomplete_kwargs,
        )

    def generate_filter_field(self, field_name: str) -> FilterField:
        return FilterField(
            field_name,
            model_field_name=self.model_field_name,
            **self.filter_kwargs,
        )
