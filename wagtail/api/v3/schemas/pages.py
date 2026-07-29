from datetime import datetime
from typing import Literal

import swapper
from django.core.exceptions import FieldDoesNotExist
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from ninja import Schema

from wagtail.api.v2.utils import get_full_url
from wagtail.models import AbstractPage

Page = swapper.load_model("wagtailcore", "Page")


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
    def resolve_meta(obj: AbstractPage, context: dict) -> PageMetaSchema:
        request = context["request"]

        try:
            path = reverse("wagtailapi_v3:detail_page", kwargs={"page_id": obj.pk})
            detail_url = get_full_url(request, path)
        except NoReverseMatch:
            detail_url = None

        try:
            html_url = obj.get_full_url(request)
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


#: Page's own fields that every concrete page type can accept on creation,
#: beyond whatever extra fields a model declares through ``api_fields``.
BASE_PAGE_FIELDS = [
    "title",
    "slug",
]
for field in ["seo_title", "search_description", "show_in_menus"]:
    try:
        Page._meta.get_field(field)
    except FieldDoesNotExist:
        pass
    else:
        BASE_PAGE_FIELDS.append(field)

BASE_PAGE_READ_FIELDS = BASE_PAGE_FIELDS + [
    "pk",
    "first_published_at",
    "locale",
]


class PageCreateMetaSchema(Schema):
    parent_id: int
    type: str
    action: Literal["publish"] | None = None


class PageCreateBaseSchema(Schema):
    meta: PageCreateMetaSchema


class PageUpdateMetaSchema(Schema):
    type: str | None = None
    action: Literal["publish"] | None = None


class PageUpdateBaseSchema(Schema):
    meta: PageUpdateMetaSchema = PageUpdateMetaSchema()
