from collections.abc import Iterable
from typing import Any, Callable, Literal, cast

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Field, ForeignKey, Model
from django.db.models.fields.reverse_related import ForeignObjectRel
from modelcluster.fields import ParentalKey
from modelcluster.models import get_all_child_relations
from ninja import Schema
from ninja.orm import create_schema
from ninja.orm.fields import get_schema_field
from taggit.managers import TaggableManager

from wagtail.api import APIField
from wagtail.fields import StreamField

#: (annotation, default), or None if the field has no defined writable shape.
InputFieldSchema = tuple[Any, Any] | None
InputFieldSchemaFunc = Callable[["InputSchemaGenerator", Field], InputFieldSchema]


class InputSchemaGenerator:
    """
    Auto-generates Ninja input (create) schemas for concrete models.

    Mirrors :class:`wagtail.api.v3.schemas.generators.read.SchemaGenerator`,
    but describes what the API accepts for writing rather than what it
    returns for reading. A field is included if it's one of the model's own
    ``fields`` (passed to ``generate_schema``) or listed in the model's
    ``api_fields``, excluding legacy API v2 custom serializer fields (those
    are read-only computed values, not real fields).
    """

    field_schemas: dict[type[Field | ForeignObjectRel], InputFieldSchemaFunc] = {}
    """
    Map of Django field classes to functions that return an
    ``(annotation, default)`` tuple for that field type, or ``None`` if the
    field type has no defined writable shape via this API.
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

    def register_field_schema(
        self,
        field_class: type[Field | ForeignObjectRel],
        func: InputFieldSchemaFunc,
    ) -> None:
        """Register a function to generate an input schema field for ``field_class``."""
        self.field_schemas[field_class] = func

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

            extra_fields = self._build_extra_fields(model, exclude=exclude)
            namespace: dict[str, Any] = {"__annotations__": {}}
            for field_name, (annotation, default) in extra_fields.items():
                namespace["__annotations__"][field_name] = annotation
                namespace[field_name] = default
            schema = cast(type[Schema], type(schema)(name, (schema,), namespace))

            self._child_relation_schema_cache[model] = schema
        return self._child_relation_schema_cache[model]

    def _build_extra_fields(
        self,
        model: type[Model],
        *,
        exclude: Iterable[str] = (),
    ) -> dict[str, tuple[Any, Any]]:
        """Return ``{field_name: (annotation, default)}`` for ``api_fields`` extras.

        Custom-serializer (legacy API v2) fields are skipped since those are
        read-only computed values with no defined writable shape. ``exclude``
        drops any field also named there - namely the housekeeping fields
        ``get_child_relation_schema`` already excludes (the ``ParentalKey``
        back to the parent, the primary key, ``sort_order``): a model's
        ``api_fields`` may list one of those (e.g. to expose the parent link
        for reading), and without this, that would silently reintroduce a
        field this API never intends to accept from the client.
        """
        exclude = set(exclude)
        extra_fields: dict[str, tuple[Any, Any]] = {}

        for field in self._normalize_api_fields(model):
            if field.name in exclude:
                continue

            if field.serializer is not None:
                continue

            try:
                model_field = model._meta.get_field(field.name)
            except FieldDoesNotExist:
                # Not a real Django field (e.g. a plain Python property) -
                # there's no defined writable shape for it, so skip it.
                continue

            # See if field's class or its parents have a registered schema
            # generator. Use it if so, otherwise treat it as a real Django
            # field (a ForeignKey, or a concrete CharField/TextField/etc).
            model_field = cast(Field, model_field)
            for cls in model_field.__class__.mro():
                cls = cast(type[Field], cls)
                if cls in self.field_schemas:
                    field_schema = self.field_schemas[cls](self, model_field)
                    if field_schema is not None:
                        extra_fields[field.name] = field_schema
                    break
            else:
                python_type, field_info = get_schema_field(model_field)
                extra_fields[field.name] = (python_type, field_info.default)

        return extra_fields

    @staticmethod
    def _narrowed_meta_schema(
        base_meta_schema: type[Schema], model: type[Model]
    ) -> type[Schema]:
        """Narrow ``base_meta_schema``'s ``type`` to a ``Literal`` for ``model``.

        A shared base class's ``meta`` field types ``type`` generically
        (e.g. ``str``), since one class is reused across every model's
        generated schema. This builds a per-model subclass that only accepts
        its own content type label instead, so the OpenAPI schema (and
        validation) reflects the actual, constant value rather than an
        open-ended string.
        """
        return cast(
            type[Schema],
            type(base_meta_schema)(
                f"{model._meta.object_name}InputMetaSchema",
                (base_meta_schema,),
                {"__annotations__": {"type": Literal[model._meta.label]}},  # ty: ignore[invalid-type-form]
            ),
        )

    def generate_schema(
        self,
        model: type[Model],
        *,
        base_class: type[Schema],
        fields: Iterable[str] = (),
        required_fields: Iterable[str] = (),
    ) -> type[Schema]:
        """Build an input (create) schema for the concrete model ``model``.

        ``fields`` names the model's own fields to always include (besides
        whatever ``api_fields`` adds) - e.g. a page's ``title``/``slug``.
        ``required_fields`` marks which of those ``fields`` must be provided;
        the rest are optional.

        If ``base_class`` declares a ``meta`` field (e.g. a schema holding
        control fields like ``parent_id`` and a ``type`` discriminator, kept
        under ``meta`` rather than at the top level so a model field sharing
        one of those names can't be silently shadowed by them - see
        :class:`wagtail.api.v3.schemas.pages.PageCreateBaseSchema`), it's
        narrowed to a ``Literal`` matching this specific model, the same way
        the read-side generator narrows ``meta.type`` for read schemas.
        """
        field_names = [
            name
            for name in fields
            if name in {f.name for f in model._meta.get_fields()}
        ]
        name = f"{model._meta.object_name}InputSchema"
        schema = create_schema(
            model,
            name=f"{name}Base",
            fields=field_names,
            optional_fields=[n for n in field_names if n not in required_fields],
            base_class=base_class,
        )

        extra_fields = self._build_extra_fields(model)
        namespace: dict[str, Any] = {"__annotations__": {}}

        meta_field = base_class.model_fields.get("meta")
        if meta_field is not None:
            namespace["__annotations__"]["meta"] = self._narrowed_meta_schema(
                meta_field.annotation, model
            )

        for field_name, (annotation, default) in extra_fields.items():
            namespace["__annotations__"][field_name] = annotation
            namespace[field_name] = default

        metaclass = type(schema)
        return cast(type[Schema], metaclass(name, (schema,), namespace))


def streamfield_schema(
    generator: InputSchemaGenerator, field: Field
) -> InputFieldSchema:
    return list[Any], []


def tags_schema(generator: InputSchemaGenerator, field: Field) -> InputFieldSchema:
    return list[str], []


def child_relation_schema(
    generator: InputSchemaGenerator, field: Field
) -> InputFieldSchema:
    field: ForeignObjectRel = cast(ForeignObjectRel, field)
    if field not in get_all_child_relations(field.model):
        # A reverse relation with no ParentalKey (i.e. not an InlinePanel
        # child) has no defined writable shape via this API, so it's
        # skipped rather than guessed at.
        return None

    child_schema = generator.get_child_relation_schema(field.related_model)
    return list[child_schema], []  # ty: ignore[invalid-type-form]


def foreign_key_schema(
    generator: InputSchemaGenerator, field: Field
) -> InputFieldSchema:
    field = cast(ForeignKey, field)
    python_type, field_info = get_schema_field(field)
    return python_type, field_info.default


generator = InputSchemaGenerator()
generator.register_field_schema(StreamField, streamfield_schema)
generator.register_field_schema(TaggableManager, tags_schema)
generator.register_field_schema(ForeignObjectRel, child_relation_schema)
generator.register_field_schema(ForeignKey, foreign_key_schema)
