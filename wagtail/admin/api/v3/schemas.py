from typing import Optional

from django.conf import settings
from django.urls import NoReverseMatch, reverse
from ninja import Field, Schema

from wagtail.api.v2.utils import get_full_url
from wagtail.api.v3.querysets import get_pages_queryset
from wagtail.api.v3.schemas import BasePageMetaSchema, BasePageSchema
from wagtail.api.v3.schemas.pages import SimpleBasePageMetaSchema, SimpleBasePageSchema
from wagtail.models import AbstractPage


class AdminSimpleBasePageMetaSchema(SimpleBasePageMetaSchema):
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


class AdminSimpleBasePageSchema(SimpleBasePageSchema):
    meta: AdminSimpleBasePageMetaSchema
    admin_display_title: str = Field(..., alias="get_admin_display_title")


class AdminBasePageMetaSchema(AdminSimpleBasePageMetaSchema, BasePageMetaSchema):
    pass


class AdminBasePageSchema(AdminSimpleBasePageSchema, BasePageSchema):
    meta: AdminBasePageMetaSchema


class AdminPageMetaSchema(AdminBasePageMetaSchema):
    live: bool
    has_unpublished_changes: bool
    status: str

    @staticmethod
    def resolve_status(obj: AbstractPage, context: dict) -> str:
        # Resolve translatable string
        return str(obj.status_string)


class AdminPageSchema(AdminBasePageSchema):
    meta: AdminPageMetaSchema


class PageChildrenSchema(Schema):
    count: int
    listing_url: str

    @staticmethod
    def resolve_count(obj: AbstractPage, context: dict) -> int:
        queryset = get_pages_queryset(context["request"])
        return queryset.child_of(obj).count()

    @staticmethod
    def resolve_listing_url(obj: AbstractPage, context: dict) -> str:
        request = context["request"]
        path = reverse("wagtailadmin_api_v3:explore_pages")
        url = path + f"?child_of={obj.pk}"
        return get_full_url(request, url)


class AdminExplorerMetaSchema(AdminPageMetaSchema):
    children: PageChildrenSchema

    @staticmethod
    def resolve_children(obj: AbstractPage, context: dict) -> AbstractPage:
        # Pass through to PageChildrenSchema
        return obj


class AdminExplorerPageSchema(AdminPageSchema):
    meta: AdminExplorerMetaSchema


class AdminPageDetailMetaSchema(AdminExplorerMetaSchema):
    parent: Optional[AdminSimpleBasePageSchema] = None
    if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
        translations: list[AdminSimpleBasePageSchema] = []

    @staticmethod
    def resolve_parent(obj: AbstractPage, context: dict):
        # Only serialize the parent if the user can explore it
        if (parent := obj.get_parent()) and not (
            get_pages_queryset(context["request"]).filter(id=parent.id).exists()
        ):
            return None
        return parent

    @staticmethod
    def resolve_translations(obj: AbstractPage, context: dict):
        return obj.get_translations()


class AdminPageDetailSchema(AdminPageSchema):
    meta: AdminPageDetailMetaSchema
