from datetime import datetime

from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from ninja import Schema

from wagtail.api.v2.utils import get_full_url
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
