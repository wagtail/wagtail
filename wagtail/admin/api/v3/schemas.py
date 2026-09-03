from typing import Optional

import swapper
from django.urls import NoReverseMatch, reverse
from ninja import Field, Schema

from wagtail.api.v2.utils import get_full_url
from wagtail.api.v3.querysets import get_pages_queryset
from wagtail.api.v3.schemas import BasePageMetaSchema, BasePageSchema, BaseSchema
from wagtail.api.v3.schemas.pages import SimpleBasePageSchema
from wagtail.models import AbstractPage

Page = swapper.load_model("wagtailcore", "Page")


class AdminPageMetaSchema(BasePageMetaSchema):
    live: bool
    has_unpublished_changes: bool
    status: str

    @staticmethod
    def resolve_status(obj: AbstractPage, context: dict) -> str:
        # Resolve translatable string
        return str(obj.status_string)

    @staticmethod
    def resolve_detail_url(obj: AbstractPage, context: dict) -> str | None:
        request = context["request"]
        try:
            path = reverse(
                "wagtailadmin_api_v3:detail_page", kwargs={"page_id": obj.pk}
            )
            return get_full_url(request, path)
        except NoReverseMatch:
            return None


class AdminPageSchema(BasePageSchema):
    meta: AdminPageMetaSchema
    admin_display_title: str = Field(..., alias="get_admin_display_title")


class PageChildrenCountSchema(Schema):
    count: int


class AdminExplorerMetaSchema(Schema):
    type: str
    parent: Optional[SimpleBasePageSchema] = None
    locale: Optional[str] = None
    children: PageChildrenCountSchema
    live: bool
    has_unpublished_changes: bool
    status: str

    @staticmethod
    def resolve_type(obj: AbstractPage, context: dict) -> str:
        return (obj.specific_class or Page)._meta.label

    @staticmethod
    def resolve_parent(obj: AbstractPage, context: dict):
        return _get_explorable_parent(obj, context)

    @staticmethod
    def resolve_locale(obj: AbstractPage, context: dict) -> str | None:
        return obj.locale.language_code if obj.locale else None

    @staticmethod
    def resolve_children(obj: AbstractPage, context: dict) -> dict:
        queryset = get_pages_queryset(context["request"])
        return {"count": queryset.child_of(obj).count()}

    @staticmethod
    def resolve_status(obj: AbstractPage, context: dict) -> str:
        return str(obj.status_string)


class AdminExplorerPageSchema(BaseSchema):
    id: int
    admin_display_title: str = Field(..., alias="get_admin_display_title")
    meta: AdminExplorerMetaSchema


def _get_explorable_parent(obj: AbstractPage, context: dict) -> Page | None:
    parent = obj.get_parent()
    if parent is None:
        return None
    queryset = get_pages_queryset(context["request"])
    if not queryset.filter(id=parent.id).exists():
        return None
    return parent
