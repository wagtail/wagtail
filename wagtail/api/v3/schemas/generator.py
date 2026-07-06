from typing import Any, Callable, cast

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Model
from django.db.models.fields import Field
from django.db.models.fields.reverse_related import ForeignObjectRel
from ninja import Schema
from ninja.errors import ConfigError
from ninja.orm import create_schema

from wagtail.api import APIField
from wagtail.fields import StreamField

FieldSchema = tuple[type, Any, Callable | None]
FieldSchemaFunc = Callable[["SchemaGenerator", Field], FieldSchema]


class SchemaGenerator:
    """
    Auto-generates Ninja read schemas for concrete models.

    Each generated schema combines a base schema with whatever extra fields a model
    declares through ``api_fields``, the mechanism used by the DRF-based API v2
    (see :mod:`wagtail.api.conf`). Plain, introspectable Django fields are typed
    via :func:`ninja.orm.create_schema`; everything else is handled on a
    best-effort basis - see ``build_schema`` for the exact rules.
    """

    field_schemas: dict[type[Field | ForeignObjectRel], FieldSchemaFunc] = {}
    """
    Map of Django field classes to functions that return a tuple of
    (annotation, default value, resolver function) for that field type.
    """

    _reverse_related_schema_cache: dict[type[Model], type[Schema]] = {}
    """
    Schemas already built for a given reverse-related model, so a model
    referenced by several models' api_fields only gets built once.
    """

    @staticmethod
    def _normalize_api_fields(model: type[Model]) -> list[APIField]:
        return [
            field if isinstance(field, APIField) else APIField(field)
            for field in getattr(model, "api_fields", ())
        ]

    def register_field_schema(
        self,
        field_class: type[Field | ForeignObjectRel],
        func: FieldSchemaFunc,
    ) -> None:
        """Register a function to generate schema fields for ``field_class``."""
        self.field_schemas[field_class] = func

    def get_reverse_related_schema(self, model: type[Model]) -> type[Schema]:
        if model not in self._reverse_related_schema_cache:
            self._reverse_related_schema_cache[model] = self.build_schema(
                model,
                name=f"{model._meta.object_name}Schema",
                base_class=Schema,
                # Prevent going too deep into nested structures.
                follow_reverse_related=False,
            )
        return self._reverse_related_schema_cache[model]

    def extend_schema(
        self,
        base: type[Schema],
        name: str,
        fields: dict[str, FieldSchema],
    ) -> type[Schema]:
        """Subclass ``base``, adding ``fields`` (and any ``resolve_*`` methods).

        Built via the base's own metaclass rather than ``pydantic.create_model``,
        since ninja only picks up ``resolve_<field>`` methods by scanning a
        class's namespace as the class is created.
        """
        namespace: dict[str, Any] = {"__annotations__": {}}
        for field_name, (annotation, default, resolver) in fields.items():
            namespace["__annotations__"][field_name] = annotation
            namespace[field_name] = default
            if resolver is not None:
                namespace[f"resolve_{field_name}"] = resolver

        metaclass = type(base)
        schema_class = metaclass(name, (base,), namespace)
        return cast(type[Schema], schema_class)

    def build_schema(
        self,
        model: type[Model],
        *,
        name: str,
        base_class: type[Schema],
        follow_reverse_related: bool,
    ) -> type[Schema]:
        """Build a schema for ``model``'s ``api_fields``, on top of ``base_class``.

        Each entry in ``api_fields`` is classified as:

        - a custom-serializer field: omitted, since inspecting arbitrary
          DRF-style serializers is out of scope for now.
        - a ``StreamField``: typed as ``Any`` and resolved via
          ``StreamValue.stream_block.get_api_representation``, matching how
          API v2 serializes StreamField values.
        - any other concrete/forward Django field: typed via ``create_schema``.
        - a reverse relation (e.g. an ``InlinePanel``'s target): resolved as
          ``list[NestedSchema]`` if ``follow_reverse_related`` is True,
          otherwise omitted. This flag caps recursion to one level deep.
        - anything else (a plain Python property, typically): typed as ``Any``
          and read straight off the instance.
        """
        real_names = []
        extra_fields: dict[str, FieldSchema] = {}

        for field in self._normalize_api_fields(model):
            # Legacy APIv2 APIField instance
            if field.serializer is not None:
                continue

            try:
                model_field = model._meta.get_field(field.name)
            except FieldDoesNotExist:
                # Not a real Django field, so treat it as a plain Python property.
                extra_fields[field.name] = (Any, None, None)
            else:
                if (
                    isinstance(model_field, ForeignObjectRel)
                    and not follow_reverse_related
                ):
                    # We're building a nested schema, don't recurse further.
                    continue

                # See if field's class or its parents have a registered schema
                # generator. Use it if so, otherwise treat it as a real Django field.
                model_field = cast(Field, model_field)
                for cls in model_field.__class__.mro():
                    cls = cast(type[Field], cls)
                    if cls in self.field_schemas:
                        schema = self.field_schemas[cls](self, model_field)
                        extra_fields[field.name] = schema
                        break
                else:
                    real_names.append(field.name)

        schema = base_class
        if real_names:
            try:
                schema = create_schema(
                    model,
                    name=f"{name}Base" if extra_fields else name,
                    fields=real_names,
                    base_class=base_class,
                )
            except ConfigError:
                # A field type create_schema can't map to a Python type (rare -
                # only concrete, non-relation, non-StreamField types can hit
                # this). Fall back to treating those fields as opaque, rather
                # than failing schema generation for the whole model.
                for field_name in real_names:
                    extra_fields.setdefault(field_name, (Any, None, None))

        if extra_fields:
            schema = self.extend_schema(schema, name, extra_fields)

        return schema

    def generate_schema(
        self,
        model: type[Model],
        base_class: type[Schema],
    ) -> type[Schema]:
        """
        Build a read schema for the concrete model ``model`` using the specified
        ``base_class``.
        """
        return self.build_schema(
            model,
            name=f"{model._meta.object_name}Schema",
            base_class=base_class,
            follow_reverse_related=True,
        )


def reverse_related_schema(generator: SchemaGenerator, field: Field) -> FieldSchema:
    field: ForeignObjectRel = cast(ForeignObjectRel, field)
    schema = generator.get_reverse_related_schema(field.related_model)
    return list[schema], [], None  # ty:ignore[invalid-type-form]


def streamfield_schema(generator: SchemaGenerator, field: Field) -> FieldSchema:
    field_name = field.name

    def resolve(obj: Model, context: dict) -> Any:
        value = getattr(obj, field_name)
        return value.stream_block.get_api_representation(value, context)

    return list[Any], [], staticmethod(resolve)


generator = SchemaGenerator()
generator.register_field_schema(ForeignObjectRel, reverse_related_schema)
generator.register_field_schema(StreamField, streamfield_schema)
