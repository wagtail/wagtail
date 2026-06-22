from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.pagination import paginate

from wagtail.api.v3.pagination import WagtailLimitOffsetPagination
from wagtail.api.v3.querysets import AccessTier, get_pages_queryset
from wagtail.api.v3.schemas import PageListingSchema, serialize_page_listing


class PageListingPagination(WagtailLimitOffsetPagination):
    """Serialize pages after Ninja slices. Skip rows that are not in the response."""

    def paginate_queryset(self, queryset, pagination, request, **params):
        result = super().paginate_queryset(queryset, pagination, request, **params)
        result["items"] = [
            serialize_page_listing(page, request) for page in result["items"]
        ]
        return result


router = Router(tags=["pages"])


def _public_pages_queryset(request: HttpRequest):
    # Stable ordering so offset/limit pagination is deterministic (v2 parity).
    return get_pages_queryset(request, tier=AccessTier.PUBLIC).order_by("id")


@router.get(
    "/",
    response=list[PageListingSchema],
    url_name="list_pages",
    summary="List pages",
    operation_id="pages_list",
)
@paginate(PageListingPagination)
def list_pages(request: HttpRequest):
    return _public_pages_queryset(request)


@router.get(
    "/{page_id}/",
    response=PageListingSchema,
    url_name="detail_page",
    summary="Page detail",
    operation_id="pages_detail",
)
def get_page(request: HttpRequest, page_id: int):
    page = get_object_or_404(_public_pages_queryset(request), pk=page_id)
    return serialize_page_listing(page.specific, request)
