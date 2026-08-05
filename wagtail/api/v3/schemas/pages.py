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


class SimpleBasePageMetaSchema(Schema):
    type: str | None = None
    detail_url: str | None = None
    html_url: str | None = None

    @staticmethod
    def resolve_type(obj: AbstractPage, context: dict) -> str | None:
        return (obj.specific_class or Page)._meta.label

    @staticmethod
    def resolve_detail_url(obj: AbstractPage, context: dict) -> str | None:
        request = context["request"]
        try:
            path = reverse("wagtailapi_v3:detail_page", kwargs={"page_id": obj.pk})
            return get_full_url(request, path)
        except NoReverseMatch:
            return None

    @staticmethod
    def resolve_html_url(obj: AbstractPage, context: dict) -> str | None:
        request = context["request"]
        try:
            return obj.get_full_url(request)
        except NoReverseMatch:
            return None


class SimpleBasePageSchema(Schema):
    id: int
    title: str
    meta: SimpleBasePageMetaSchema

    @staticmethod
    def resolve_meta(obj: AbstractPage, context: dict) -> AbstractPage:
        # Pass through so resolve_* methods on meta schema works with the page
        return obj


class BasePageMetaSchema(SimpleBasePageMetaSchema):
    locale: str | None = None
    slug: str
    first_published_at: datetime | None = None

    @staticmethod
    def resolve_locale(obj: AbstractPage, context: dict) -> str | None:
        return obj.locale.language_code if obj.locale else None


class BasePageSchema(SimpleBasePageSchema):
    meta: BasePageMetaSchema


class PageMetaSchema(BasePageMetaSchema):
    alias_of: SimpleBasePageSchema | None = None
    parent: SimpleBasePageSchema | None = None

    @staticmethod
    def resolve_parent(obj: AbstractPage, context: dict) -> AbstractPage | None:
        return obj.get_parent()


class PageSchema(BasePageSchema):
    meta: PageMetaSchema


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
