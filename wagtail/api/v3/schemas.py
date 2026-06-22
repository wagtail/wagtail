from datetime import datetime
from typing import cast

from django.http import HttpRequest
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
    first_published_at: str | None = None


class PageListingSchema(Schema):
    id: int
    title: str
    meta: PageMetaSchema


class ContentTypeSummarySchema(Schema):
    name: str
    label: str


def get_page_type_name(page: Page) -> str | None:
    if page.specific_class is None:
        return None
    return page.specific_class._meta.label


def get_page_detail_url(request: HttpRequest, page: Page) -> str | None:
    try:
        path = reverse("wagtailapi_v3:detail_page", kwargs={"page_id": page.pk})
    except NoReverseMatch:
        return None
    return get_full_url(request, path)


def serialize_page_listing(page: Page, request: HttpRequest) -> PageListingSchema:
    """Serialize a page for list or detail responses.

    List views pass base ``Page`` instances and resolve ``meta.type`` via
    ``specific_class`` (no extra query per row). Detail passes ``page.specific``
    so typed fields can be added to the schema later without changing call sites.
    """
    try:
        html_url = page.full_url
    except NoReverseMatch:
        html_url = None

    first_published_at = cast(datetime | None, page.first_published_at)
    return PageListingSchema(
        id=page.pk,
        title=str(page.title),
        meta=PageMetaSchema(
            type=get_page_type_name(page),
            detail_url=get_page_detail_url(request, page),
            html_url=html_url,
            slug=str(page.slug),
            first_published_at=(
                first_published_at.isoformat() if first_published_at else None
            ),
        ),
    )
