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

#: Page's own fields that every concrete page type can accept on creation,
#: beyond whatever extra fields a model declares through ``api_fields``.
PAGE_BASE_WRITABLE_FIELDS = (
    "title",
    "slug",
    "seo_title",
    "search_description",
    "show_in_menus",
)

#: (annotation, default), or None if the field has no defined writable shape.
InputFieldSchema = tuple[Any, Any] | None
InputFieldSchemaFunc = Callable[["InputSchemaGenerator", Field], InputFieldSchema]


class PageCreateMetaSchema(Schema):
    parent_id: int
    type: str


class PageCreateBaseSchema(Schema):
    meta: PageCreateMetaSchema


class InputSchemaGenerator:
    """
    Auto-generates Ninja input (create) schemas for concrete page models.

    Mirrors :class:`wagtail.api.v3.schemas.generator.SchemaGenerator`, but
    describes what the API accepts for writing rather than what it returns
    for reading. A field is included if it is one of ``PAGE_BASE_WRITABLE_FIELDS``
    or listed in the model's ``api_fields``, excluding legacy API v2 custom
    serializer fields (those are read-only computed values, not real fields).
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

            extra_fields = self._build_extra_fields(model)
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

    def generate_schema(self, model: type[Model]) -> type[Schema]:
        """Build an input (create) schema for the concrete page model ``model``.

        Includes a ``meta`` field holding ``parent_id`` (the page to create
        the new page under) and ``type`` (the page model's content type
        label, narrowed to a ``Literal`` for this specific model), nested
        under ``meta`` - mirroring the read-side response's own
        ``meta.type``/``meta.slug`` convention - rather than sitting at the
        top level alongside the page model's own fields, so a model with a
        field literally named ``parent_id`` or ``type`` (e.g. a CharField
        choice named "type") can't have it silently shadowed by our control
        fields.
        """
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

        meta_schema = cast(
            type[Schema],
            type(PageCreateMetaSchema)(
                f"{model._meta.object_name}InputMetaSchema",
                (PageCreateMetaSchema,),
                {"__annotations__": {"type": Literal[model._meta.label]}},  # ty: ignore[invalid-type-form]
            ),
        )
        extra_fields = self._build_extra_fields(model)
        namespace: dict[str, Any] = {"__annotations__": {"meta": meta_schema}}
        for field_name, (annotation, default) in extra_fields.items():
            namespace["__annotations__"][field_name] = annotation
            namespace[field_name] = default

        metaclass = type(schema)
        return cast(
            type[Schema],
            metaclass(name, (PageCreateBaseSchema, schema), namespace),
        )


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


input_generator = InputSchemaGenerator()
input_generator.register_field_schema(StreamField, streamfield_schema)
input_generator.register_field_schema(TaggableManager, tags_schema)
input_generator.register_field_schema(ForeignObjectRel, child_relation_schema)
input_generator.register_field_schema(ForeignKey, foreign_key_schema)
