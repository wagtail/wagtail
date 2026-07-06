from collections.abc import Iterable
from datetime import datetime
from typing import Annotated, Any, Union

from django.db.models import Model
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from ninja import Schema
from pydantic import Discriminator, Tag

from wagtail.api.v2.utils import get_full_url
from wagtail.api.v3.schemas import generator
from wagtail.models import Page


class PageMetaSchema(Schema):
    type: str | None = None
    detail_url: str | None = None
    html_url: str | None = None
    slug: str
    first_published_at: datetime | None = None


class BasePageSchema(Schema):
    id: int
    title: str
    meta: PageMetaSchema

    @staticmethod
    def resolve_meta(obj: Page, context: dict) -> PageMetaSchema:
        request = context["request"]

        try:
            path = reverse("wagtailapi_v3:detail_page", kwargs={"page_id": obj.pk})
            detail_url = get_full_url(request, path)
        except NoReverseMatch:
            detail_url = None

        try:
            html_url = obj.full_url
        except NoReverseMatch:
            html_url = None

        return PageMetaSchema(
            type=obj.specific_class and obj.specific_class._meta.label,
            detail_url=detail_url,
            html_url=html_url,
            slug=obj.slug,
            first_published_at=obj.first_published_at,
        )


def _discriminate_page_schema(value: Any) -> str | None:
    """Pick the page-detail union member matching ``value``'s content type.

    A plain ``Union`` of every page schema isn't safe here: Pydantic's smart
    union mode picks a member by attribute-match heuristics, and since most
    of our generated extra fields default to ``None``, an instance of one
    page model can validate against another model's schema just as well.

    This discriminator instead keys directly off the page's content type
    label (matching the registry's keys). It runs at two different stages,
    so it has to handle two different shapes of ``value``:

    - during validation, ``value`` is the raw page instance returned by the
      view (or a dict, for OpenAPI-style validation from JSON);
    - during serialization, ``value`` is already a built schema instance,
      whose ``meta.type`` was set by ``BasePageSchema.resolve_meta``.
    """
    if isinstance(value, dict):
        meta = value.get("meta") or {}
        return meta.get("type")

    meta = getattr(value, "meta", None)
    if meta is not None:
        return meta.get("type") if isinstance(meta, dict) else meta.type

    return type(value)._meta.label


def build_page_schema_union(models: Iterable[type[Model]]) -> Any:
    """Build a response type covering every model's generated page schema.

    Each model's schema is tagged with its content type label and resolved
    through :func:`_discriminate_page_schema`, rather than relying on
    Pydantic to guess the right member from field overlap alone.
    """
    models = list(models)
    if len(models) == 1:
        return generator.generate_schema(models[0], base_class=BasePageSchema)

    members = tuple(
        Annotated[
            generator.generate_schema(  # ty: ignore[invalid-type-form]
                model,
                base_class=BasePageSchema,
            ),
            Tag(model._meta.label),
        ]
        for model in models
    )
    return Annotated[
        Union[members],  # ty: ignore[invalid-type-form]
        Discriminator(_discriminate_page_schema),
    ]
