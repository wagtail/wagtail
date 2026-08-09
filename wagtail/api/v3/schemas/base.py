from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any, Iterable, Union

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from ninja import Schema
from pydantic import Discriminator, Tag


class BaseMetaSchema(Schema):
    type: str | None = None


class BaseSchema(Schema):
    meta: BaseMetaSchema

    @staticmethod
    def resolve_meta(obj: Model) -> BaseMetaSchema:
        return BaseMetaSchema(type=obj._meta.label)


class ContentTypeSummarySchema(Schema):
    name: str
    label: str


def discriminate_schema(value: Any) -> str | None:
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
        return meta.get("type")

    meta = getattr(value, "meta", None)
    if meta is not None:
        return meta.get("type") if isinstance(meta, dict) else meta.type

    return type(value)._meta.label


def build_discriminated_union(
    models: list[type[Model]],
    schema_for: Callable[[type[Model]], type[Any]],
) -> Any:
    """Build a union of ``schema_for(model)`` over ``models``, tagged and
    resolved by ``discriminator`` - or just the one schema if there's only
    one model, since a single-member union is redundant.
    """
    if len(models) == 1:
        return schema_for(models[0])

    members = tuple(
        Annotated[schema_for(model), Tag(model._meta.label)]  # ty: ignore[invalid-type-form]
        for model in models
    )
    return Annotated[
        Union[members],  # ty: ignore[invalid-type-form]
        Discriminator(discriminate_schema),
    ]


@dataclass(frozen=True)
class DiscriminatedUnionSchemas:
    """Discriminated-union schemas to be used by a generic router."""

    detail: Any
    create: Any
    update: Any


def build_union_schemas(models: Iterable[type[Model]]) -> DiscriminatedUnionSchemas:
    """Build the detail, create, and update unions for ``models`` together.

    The detail union tags each model's schema, generated fresh here, with
    its content type label and resolves it through
    :func:`discriminate_schema` - Pydantic's smart union mode can't be
    trusted to guess the right member from field overlap alone, since most
    of our generated extra fields default to ``None``.
    """

    from wagtail.api.v3.registry import registry

    def registered_schema_for(model: type[Model], attr: str):
        registration = registry.get(model._meta.label)
        schema = registration and getattr(registration, attr)
        if schema is None:
            raise ImproperlyConfigured(
                f"{model._meta.label} has no registered {attr} - "
                f"ContentTypeRegistry.register_defaults() must run before "
                f"build_union_schemas()."
            )
        return schema

    models = list(models)
    return DiscriminatedUnionSchemas(
        detail=build_discriminated_union(
            models,
            lambda model: registered_schema_for(model, "read_schema"),
        ),
        create=build_discriminated_union(
            models,
            lambda model: registered_schema_for(model, "create_schema"),
        ),
        update=build_discriminated_union(
            models,
            lambda model: registered_schema_for(model, "patch_schema"),
        ),
    )
