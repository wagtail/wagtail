from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Any, Literal, Union

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from ninja import Schema
from pydantic import Discriminator, Tag

from wagtail.api.v2.utils import get_full_url
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


def _build_discriminated_union(
    models: list[type[Model]],
    schema_for: Callable[[type[Model]], type[Any]],
    discriminator: Callable[[Any], str | None],
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
        Discriminator(discriminator),
    ]


#: Page's own fields that every concrete page type can accept on creation,
#: beyond whatever extra fields a model declares through ``api_fields``.
PAGE_CREATE_FIELDS = (
    "title",
    "slug",
    "seo_title",
    "search_description",
    "show_in_menus",
)


class PageCreateMetaSchema(Schema):
    parent_id: int
    type: str
    action: Literal["publish"] | None = None


class PageCreateBaseSchema(Schema):
    meta: PageCreateMetaSchema


class PageUpdateMetaSchema(Schema):
    type: str
    action: Literal["publish"] | None = None


class PageUpdateBaseSchema(Schema):
    meta: PageUpdateMetaSchema


@dataclass(frozen=True)
class PageSchemaUnions:
    """The three discriminated-union schemas the pages router needs, built
    together over one pass of the page models.

    :attr:`detail` covers every model's generated response schema, so the
    detail endpoint's response accurately reflects whichever specific page
    type was requested, instead of only the fields ``BasePageSchema`` has.
    :attr:`create` and :attr:`update` cover every model's registered
    create/patch schema, so the create and update endpoints accept whichever
    fields are valid for the specific page type named by their ``"type"``
    field.
    """

    detail: Any
    create: Any
    update: Any


def build_page_schema_unions(models: Iterable[type[Model]]) -> PageSchemaUnions:
    """Build the detail, create and update unions for ``models`` together.

    The detail union tags each model's schema, generated fresh here, with
    its content type label and resolves it through
    :func:`_discriminate_page_schema` - Pydantic's smart union mode can't be
    trusted to guess the right member from field overlap alone, since most
    of our generated extra fields default to ``None``.

    The create and update unions instead read each model's ``create_schema``
    / ``patch_schema`` off the registry (populated by
    ``ContentTypeRegistry.register_defaults``) rather than generating them
    again here: two independently generated schemas for the same model and
    ``base_class`` would be distinct Python objects sharing one class
    ``__name__``, and ninja/pydantic key OpenAPI components by that name - so
    whichever one got built second would silently shadow the other in the
    generated docs. Both resolve through the same
    :func:`_discriminate_page_write_schema`, since they key off the same
    ``meta.type`` shape; the update union has no ``parent_id`` since an
    update doesn't move the page in the tree, and marks no field required,
    since it's a PATCH-style partial update where an absent field must be
    left untouched rather than rejected or cleared - the view reads which
    fields were actually supplied via ``exclude_unset``.
    """
    from wagtail.api.v3.registry import registry

    def registered_schema_for(model: type[Model], attr: str):
        registration = registry.get(model._meta.label)
        schema = registration and getattr(registration, attr)
        if schema is None:
            raise ImproperlyConfigured(
                f"{model._meta.label} has no registered {attr} - "
                f"ContentTypeRegistry.register_defaults() must run before "
                f"build_page_schema_unions()."
            )
        return schema

    models = list(models)
    return PageSchemaUnions(
        detail=_build_discriminated_union(
            models,
            lambda model: registered_schema_for(model, "read_schema"),
            _discriminate_page_schema,
        ),
        create=_build_discriminated_union(
            models,
            lambda model: registered_schema_for(model, "create_schema"),
            _discriminate_page_schema,
        ),
        update=_build_discriminated_union(
            models,
            lambda model: registered_schema_for(model, "patch_schema"),
            _discriminate_page_schema,
        ),
    )
