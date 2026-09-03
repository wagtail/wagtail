import swapper
from django.urls import NoReverseMatch, reverse
from ninja import Field

from wagtail.api.v2.utils import get_full_url
from wagtail.api.v3.querysets import get_pages_queryset
from wagtail.api.v3.schemas import BasePageMetaSchema, BasePageSchema
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


def _get_explorable_parent(obj: AbstractPage, context: dict) -> Page | None:
    """
    The page's parent, but only if it is explorable by the current user
    (mirrors the v2 admin API's PageParentField, so the root page does not
    appear for users who cannot explore it).
    """
    parent = obj.get_parent()
    if parent is None:
        return None
    queryset = get_pages_queryset(context["request"])
    if not queryset.filter(id=parent.id).exists():
        return None
    return parent
