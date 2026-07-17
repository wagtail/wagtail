from typing import Any, cast

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Model
from django.db.models.fields.reverse_related import ForeignObjectRel
from modelcluster.fields import ParentalKey
from modelcluster.models import get_all_child_relations
from ninja import Schema
from ninja.orm import create_schema
from ninja.orm.fields import get_schema_field
from taggit.managers import TaggableManager

from wagtail.api import APIField
from wagtail.fields import StreamField

#: Page's own fields that every concrete page type can accept on creation,
#: beyond whatever extra fields a model declares through ``api_fields``.
PAGE_BASE_WRITABLE_FIELDS = (
    "title",
    "slug",
    "seo_title",
    "search_description",
    "show_in_menus",
)


class InputSchemaGenerator:
    """
    Auto-generates Ninja input (create) schemas for concrete page models.

    Mirrors :class:`wagtail.api.v3.schemas.generator.SchemaGenerator`, but
    describes what the API accepts for writing rather than what it returns
    for reading. A field is included if it is one of ``PAGE_BASE_WRITABLE_FIELDS``
    or listed in the model's ``api_fields``, excluding legacy API v2 custom
    serializer fields (those are read-only computed values, not real fields).
    """

    _child_relation_schema_cache: dict[type[Model], type[Schema]] = {}
    """
    Input schemas already built for a child relation's related model (the
    "one" side of a ParentalKey, e.g. a carousel item), keyed by that model.
    """

    @staticmethod
    def _normalize_api_fields(model: type[Model]) -> list[APIField]:
        return [
            field if isinstance(field, APIField) else APIField(field)
            for field in getattr(model, "api_fields", ())
        ]

    def get_child_relation_schema(self, model: type[Model]) -> type[Schema]:
        """Build an input schema for a child relation's related model.

        Includes the related model's own editable, concrete fields (skipping
        the ``ParentalKey`` back to the parent, and the ``id``/``sort_order``
        housekeeping fields), plus its own ``api_fields`` extras (e.g. a
        StreamField nested inside an InlinePanel-managed model).
        """
        if model not in self._child_relation_schema_cache:
            exclude = {model._meta.pk.name, "sort_order"}
            for field in model._meta.get_fields():
                if isinstance(field, ParentalKey):
                    exclude.add(field.name)
                elif not (getattr(field, "concrete", False) and field.editable) or (
                    isinstance(field, StreamField)
                ):
                    exclude.add(field.name)

            name = f"{model._meta.object_name}InputSchema"
            schema = create_schema(
                model,
                name=f"{name}Base",
                exclude=list(exclude),
                base_class=Schema,
            )

            extra_fields = self._build_extra_fields(model)
            if extra_fields:
                namespace: dict[str, Any] = {"__annotations__": {}}
                for field_name, (annotation, default) in extra_fields.items():
                    namespace["__annotations__"][field_name] = annotation
                    namespace[field_name] = default
                schema = cast(type[Schema], type(schema)(name, (schema,), namespace))

            self._child_relation_schema_cache[model] = schema
        return self._child_relation_schema_cache[model]

    def _build_extra_fields(self, model: type[Model]) -> dict[str, tuple[Any, Any]]:
        """Return ``{field_name: (annotation, default)}`` for ``api_fields`` extras.

        Custom-serializer (legacy API v2) fields are skipped since those are
        read-only computed values with no defined writable shape.
        """
        extra_fields: dict[str, tuple[Any, Any]] = {}

        for field in self._normalize_api_fields(model):
            if field.serializer is not None:
                continue

            try:
                model_field = model._meta.get_field(field.name)
            except FieldDoesNotExist:
                # Not a real Django field (e.g. a plain Python property) -
                # there's no defined writable shape for it, so skip it.
                continue

            if isinstance(model_field, StreamField):
                extra_fields[field.name] = (list[Any], [])
            elif isinstance(model_field, TaggableManager):
                extra_fields[field.name] = (list[str], [])
            elif isinstance(
                model_field, ForeignObjectRel
            ) and model_field in get_all_child_relations(model):
                child_schema = self.get_child_relation_schema(model_field.related_model)
                extra_fields[field.name] = (
                    list[child_schema],  # ty: ignore[invalid-type-form]
                    [],
                )
            elif isinstance(model_field, ForeignObjectRel):
                # Any other reverse relation (a plain ForeignObjectRel with no
                # ParentalKey) has no defined writable shape via this API, so
                # it's skipped rather than guessed at.
                continue
            else:
                # A ForeignKey, or any other concrete Django field
                # (CharField, TextField, RichTextField, IntegerField, ...).
                python_type, field_info = get_schema_field(model_field)
                extra_fields[field.name] = (python_type, field_info.default)

        return extra_fields

    def generate_schema(self, model: type[Model]) -> type[Schema]:
        """Build an input (create) schema for the concrete page model ``model``."""
        base_names = [
            name
            for name in PAGE_BASE_WRITABLE_FIELDS
            if name in {f.name for f in model._meta.get_fields()}
        ]
        name = f"{model._meta.object_name}InputSchema"
        schema = create_schema(
            model,
            name=f"{name}Base",
            fields=base_names,
            optional_fields=[n for n in base_names if n != "title"],
            base_class=Schema,
        )

        extra_fields = self._build_extra_fields(model)
        if not extra_fields:
            return schema

        namespace: dict[str, Any] = {"__annotations__": {}}
        for field_name, (annotation, default) in extra_fields.items():
            namespace["__annotations__"][field_name] = annotation
            namespace[field_name] = default

        metaclass = type(schema)
        return cast(type[Schema], metaclass(name, (schema,), namespace))


input_generator = InputSchemaGenerator()
