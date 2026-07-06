from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.pagination import paginate

from wagtail.api.v3.pagination import WagtailLimitOffsetPagination
from wagtail.api.v3.querysets import AccessTier, get_pages_queryset
from wagtail.api.v3.schemas import BasePageSchema, build_page_schema_union
from wagtail.models import get_page_models

router = Router(tags=["pages"])

#: A discriminated union of every concrete page model's generated schema,
#: so the detail endpoint's response accurately reflects whichever specific
#: page type was requested, instead of only the fields BasePageSchema has.
PageDetailSchema = build_page_schema_union(get_page_models())


def _public_pages_queryset(request: HttpRequest):
    # Stable ordering so offset/limit pagination is deterministic (v2 parity).
    return get_pages_queryset(request, tier=AccessTier.PUBLIC).order_by("id")


@router.get(
    "/",
    response=list[BasePageSchema],
    url_name="list_pages",
    summary="List pages",
    operation_id="pages_list",
)
@paginate(WagtailLimitOffsetPagination)
def list_pages(request: HttpRequest):
    return _public_pages_queryset(request)


@router.get(
    "/{page_id}/",
    response=PageDetailSchema,
    url_name="detail_page",
    summary="Page detail",
    operation_id="pages_detail",
)
def get_page(request: HttpRequest, page_id: int):
    page = get_object_or_404(_public_pages_queryset(request), pk=page_id)
    return page.specific
