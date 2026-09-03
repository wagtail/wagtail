from typing import Literal, Optional, Union, cast

import swapper
from django.db.models import Model, Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Query, Router
from ninja.pagination import paginate
from pydantic import PositiveInt

from wagtail import hooks
from wagtail.api.v3.pagination import WagtailLimitOffsetPagination
from wagtail.api.v3.querysets import get_pages_queryset
from wagtail.api.v3.routers.pages import (
    OrderingSchema,
    PageFilterSchema,
    SearchSchema,
    custom_filter,
)
from wagtail.api.v3.schemas.pages import BASE_PAGE_READ_FIELDS
from wagtail.api.v3.schemas.params import APIFieldFilterSchema
from wagtail.query import PageQuerySet

from .schemas import (
    AdminExplorerPageSchema,
    AdminPageDetailSchema,
    AdminPageSchema,
)

Page = swapper.load_model("wagtailcore", "Page")

router = Router(tags=["pages"])


class AdminPageFilterSchema(PageFilterSchema):
    has_children: Optional[bool] = None

    # No-op Q so ninja doesn't attempt a default `has_children` exact lookup
    filter_has_children = custom_filter

    def apply_custom_filters(self, request: HttpRequest, queryset):
        queryset = super().apply_custom_filters(request, queryset)
        if self.has_children is not None:
            queryset = queryset.filter(
                Q(numchild__gt=0) if self.has_children else Q(numchild=0)
            )
        return queryset


@router.get(
    "/explore/",
    response=list[AdminExplorerPageSchema],
    url_name="explore_pages",
    summary="List child pages for the page explorer",
    operation_id="pages_explore",
)
@paginate(
    WagtailLimitOffsetPagination,
    pass_parameter="pagination_info",  # noqa: S106 not a password
)
def explore_pages(
    request: HttpRequest,
    child_of: Union[PositiveInt, Literal["root"]],
    **kwargs,
):
    if child_of == "root":
        parent = Page.get_first_root_node()
    else:
        parent = get_object_or_404(get_pages_queryset(request), pk=child_of)

    queryset = get_pages_queryset(request).child_of(parent)
    for hook in hooks.get_hooks("construct_explorer_page_queryset"):
        queryset = hook(parent, queryset, request)
    return queryset.defer_streamfields().specific()


@router.get(
    "/{page_id}/",
    response=AdminPageDetailSchema,
    url_name="detail_page",
    summary="Page detail",
    operation_id="pages_detail",
)
def get_page(request: HttpRequest, page_id: int):
    page = get_object_or_404(get_pages_queryset(request), pk=page_id)
    return page.specific


@router.get(
    "/",
    response=list[AdminPageSchema],
    url_name="list_pages",
    summary="List pages",
    operation_id="pages_list",
)
@paginate(
    WagtailLimitOffsetPagination,
    pass_parameter="pagination_info",  # noqa: S106 not a password
)
def list_pages(
    request: HttpRequest,
    filters: AdminPageFilterSchema = Query(...),  # ty: ignore[call-non-callable]
    ordering: OrderingSchema = Query(...),  # ty: ignore[call-non-callable]
    search: SearchSchema = Query(...),  # ty: ignore[call-non-callable]
    **kwargs,
):
    pagination_info = cast(
        WagtailLimitOffsetPagination.Input,
        kwargs.get("pagination_info"),
    )
    models = cast(list[type[Model]], filters.type)
    model = models[0] if len(models) == 1 else Page
    field_filter = APIFieldFilterSchema.with_exclude_schemas(
        raw_params=request.GET,
        schemas=(AdminPageFilterSchema, OrderingSchema, SearchSchema),
        base_fields=BASE_PAGE_READ_FIELDS,
    )
    # The root page is never returned by the admin listing (matches the v2
    # admin API's default behavior without include_root)
    queryset = cast(PageQuerySet, get_pages_queryset(request, model).exclude(depth=1))
    queryset = filters.filter(queryset, request)
    queryset = field_filter.filter_queryset(queryset)
    queryset = ordering.order_queryset(
        queryset,
        pagination_info,
        base_fields=BASE_PAGE_READ_FIELDS,
    )
    queryset = search.search_queryset(request, queryset)
    return cast(PageQuerySet, queryset).defer_streamfields().specific()
