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
from wagtail.api.v3.schemas.input_generator import input_generator
from wagtail.models import Page


class PageMetaSchema(Schema):
    type: str | None = None
    detail_url: str | None = None
    html_url: str | None = None
    locale: str | None = None
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
            # specific_class reflects obj's real content type even when obj
            # itself hasn't been upcast via .specific (e.g. in a listing).
            # If the content type's model class is missing entirely,
            # specific_class is None - get_specific() would then fall back
            # to returning the page as a plain Page instance, so Page's own
            # label is the correct fallback here too, rather than None.
            type=(obj.specific_class or Page)._meta.label,
            detail_url=detail_url,
            html_url=html_url,
            locale=obj.locale and obj.locale.language_code,
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
    Pydantic to guess the right member from field overlap alone. ``meta.type``
    on each member is narrowed to that model's own label by
    ``generator.generate_schema`` itself.
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


def _discriminate_page_create_schema(value: Any) -> str | None:
    """Pick the page-create union member matching ``value``'s ``meta.type``.

    Runs during validation, where ``value`` is the raw request dict (parsed
    JSON), so ``meta`` is itself still a plain dict at this point.
    """
    if isinstance(value, dict):
        meta = value.get("meta") or {}
        return meta.get("type") if isinstance(meta, dict) else meta.type

    meta = getattr(value, "meta", None)
    return getattr(meta, "type", None)


def build_page_input_schema_union(models: Iterable[type[Model]]) -> Any:
    """Build a request type covering every model's generated input schema.

    Every member includes a ``meta`` field holding ``parent_id`` (the page to
    create the new page under) and ``type`` (the page model's content type
    label, e.g. ``"tests.SimplePage"``), which together pick the specific
    page model to create - the same discriminator value used by the read-side
    union and ``meta.type`` in responses. ``meta`` itself is added by
    ``input_generator.generate_schema``.
    """
    models = list(models)
    if len(models) == 1:
        return input_generator.generate_schema(models[0])

    members = tuple(
        Annotated[
            input_generator.generate_schema(model),  # ty: ignore[invalid-type-form]
            Tag(model._meta.label),
        ]
        for model in models
    )
    return Annotated[
        Union[members],  # ty: ignore[invalid-type-form]
        Discriminator(_discriminate_page_create_schema),
    ]
