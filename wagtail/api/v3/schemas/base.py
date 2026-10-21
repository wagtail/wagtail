from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any, Iterable, Union

from django.db.models import Model
from ninja import Schema
from pydantic import Discriminator, Field, Tag
from typing_extensions import TypeAliasType

from wagtail.admin.rich_text.converters.db_html import RichTextRemoval


class BaseMetaSchema(Schema):
    type: str
    warnings: list[RichTextRemoval | str] | None = Field(
        None, exclude_if=lambda v: not v
    )

    @staticmethod
    def resolve_type(obj: Model, context: dict) -> str:
        return obj._meta.label

    @staticmethod
    def resolve_warnings(obj: Model, context: dict) -> list[str] | None:
        return getattr(obj, "_meta_warnings", [])


class BaseSchema(Schema):
    meta: BaseMetaSchema

    @staticmethod
    def resolve_meta(obj: Model) -> Model:
        # Pass through so resolve_* methods on meta schema works with the model
        return obj


class BaseCreateMetaSchema(Schema):
    type: str


class BaseCreateSchema(Schema):
    meta: BaseCreateMetaSchema


class BaseUpdateMetaSchema(Schema):
    type: str | None = None


class BaseUpdateSchema(Schema):
    meta: BaseUpdateMetaSchema | None = BaseUpdateMetaSchema()


class ContentTypeSummarySchema(Schema):
    name: str
    label: str


def discriminate_meta_type(value: Any) -> str | None:
    """Pick the union member matching ``value``'s content type.

    A plain ``Union`` of every schema isn't safe here: Pydantic's smart
    union mode picks a member by attribute-match heuristics, and since most
    of our generated extra fields default to ``None``, an instance of one
    model can validate against another model's schema just as well.

    This discriminator instead keys directly off the model's content type
    label (matching the registry's keys). It runs at two different stages,
    so it has to handle two different shapes of ``value``:

    - during validation, ``value`` is the raw model instance returned by the
      view (or a dict, for OpenAPI-style validation from JSON);
    - during serialization, ``value`` is already a built schema instance,
      whose ``meta.type`` was set by ``BaseSchema.resolve_meta``.
    """
    if isinstance(value, dict):
        meta = value.get("meta") or {}
        return meta.get("type", "") if isinstance(meta, dict) else str(meta)

    meta = getattr(value, "meta", None)
    if meta is not None:
        return meta.get("type") if isinstance(meta, dict) else meta.type

    return type(value)._meta.label


def build_discriminated_union(
    models: list[type[Model]],
    schema_for: Callable[[type[Model]], type[Any]],
    name: str | None = None,
) -> Any:
    """Build a union of ``schema_for(model)`` over ``models``, tagged and
    resolved by ``discriminator`` - or just the one schema if there's only
    one model, since a single-member union is redundant.

    If ``name`` is given, the union is defined as a type alias with that name,
    so that it's a named component in the OpenAPI schema. Ninja also derives
    the name of a paginated list's schema from it (e.g. ``Paged{name}``),
    which would otherwise be the same ``PagedAnnotated`` for every union.
    """
    if len(models) == 1:
        return schema_for(models[0])

    members = tuple(
        Annotated[schema, Tag(model._meta.label)]  # ty: ignore[invalid-type-form]
        for model in models
        if (schema := schema_for(model)) is not None
    )
    union = Annotated[
        Union[members],  # ty: ignore[invalid-type-form]
        Discriminator(discriminate_meta_type),
        # Ideally, we'd use the proper "discriminator" OpenAPI field here, but
        # it only supports a field on the same level as the union, while our
        # "type" is nested under "meta". (Pydantic would also automatically add
        # it if we did not use a callable discriminator.)
        Field(
            json_schema_extra={
                "description": (
                    "A union of models, discriminated by the content type in "
                    "`meta.type`."
                )
            }
        ),
    ]
    if name:
        return TypeAliasType(name, union)  # ty: ignore[invalid-type-alias-type]
    return union


@dataclass(frozen=True)
class DiscriminatedUnionSchemas:
    """Discriminated-union schemas to be used by a generic router."""

    detail: Any
    create: Any
    update: Any


def build_union_schemas(
    models: Iterable[type[Model]],
    name: str | None = None,
) -> DiscriminatedUnionSchemas:
    """Build the detail, create, and update unions for ``models`` together.

    The detail union tags each model's schema, generated fresh here, with
    its content type label and resolves it through
    :func:`discriminate_meta_type` - Pydantic's smart union mode can't be
    trusted to guess the right member from field overlap alone, since most
    of our generated extra fields default to ``None``.

    If ``name`` is given, the unions are named ``{name}DetailUnion``,
    ``{name}CreateUnion``, and ``{name}UpdateUnion``. The ``Union`` suffix
    avoids clashes with the per-model schemas, which end with ``Schema``.
    """

    from wagtail.api.v3.registry import registry

    def registered_schema_for(model: type[Model], attr: str):
        registration = registry.get(model._meta.label)
        schema = registration and getattr(registration, attr)
        return schema

    models = list(models)
    return DiscriminatedUnionSchemas(
        detail=build_discriminated_union(
            models,
            lambda model: registered_schema_for(model, "read_schema"),
            name=name and f"{name}DetailUnion",
        ),
        create=build_discriminated_union(
            models,
            lambda model: registered_schema_for(model, "create_schema"),
            name=name and f"{name}CreateUnion",
        ),
        update=build_discriminated_union(
            models,
            lambda model: registered_schema_for(model, "patch_schema"),
            name=name and f"{name}UpdateUnion",
        ),
    )
