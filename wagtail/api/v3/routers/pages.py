import functools
import json
from typing import Annotated, Literal, Optional, TypeAlias, cast

import swapper
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, Q, QuerySet
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from ninja import Body, FilterLookup, FilterSchema, Query, Router, Schema, Status
from ninja.decorators import decorate_view
from ninja.pagination import paginate
from pydantic import PositiveInt, ValidationError, field_validator, model_validator

from wagtail.actions.create_page import CreatePageAction
from wagtail.actions.edit_page import EditPageAction
from wagtail.api.v3.form_data import build_page_form, build_page_update_form
from wagtail.api.v3.pagination import WagtailLimitOffsetPagination
from wagtail.api.v3.permissions import require_any_permission
from wagtail.api.v3.querysets import AccessTier, get_pages_queryset
from wagtail.api.v3.schemas import BasePageSchema
from wagtail.api.v3.schemas.base import build_union_schemas
from wagtail.api.v3.schemas.pages import BASE_PAGE_READ_FIELDS, PageUpdateBaseSchema
from wagtail.api.validators import OrderingValidator
from wagtail.coreutils import resolve_model_string
from wagtail.models import Site, get_page_models
from wagtail.query import PageQuerySet

Page = swapper.load_model("wagtailcore", "Page")
router = Router(tags=["pages"])

page_models = get_page_models()
PageTypeLiteral = Literal[tuple(model._meta.label for model in page_models)]  # ty: ignore[invalid-type-form]
_page_schemas = build_union_schemas(page_models)
PageDetailSchema = _page_schemas.detail
PageCreateSchema = _page_schemas.create
PageUpdateSchema = _page_schemas.update


def _public_pages_queryset(request: HttpRequest, model=Page):
    # Stable ordering so offset/limit pagination is deterministic (v2 parity).
    return get_pages_queryset(request, tier=AccessTier.PUBLIC, model=model).order_by(
        "id"
    )


def default_meta_type(func):
    """
    A decorator to fill in a missing ``meta.type`` on the request body from the
    page being updated, so callers can omit it.

    This must run in VIEW mode to fill in the type before the request body is
    parsed into a Pydantic model with the discriminated union schema.
    """

    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            parsed = PageUpdateBaseSchema.model_validate_json(request.body)
        except ValidationError:
            parsed = None

        # Only do this when the type is not supplied, as it impacts performance.
        if parsed is not None and not parsed.meta.type:
            page_id = kwargs.get("page_id")
            ct_ids = Page.objects.values_list("content_type_id", flat=True)
            content_type_id = get_object_or_404(ct_ids, pk=page_id)
            content_type = ContentType.objects.get_for_id(content_type_id)
            # HACK: deserialize, fill in the type, and reserialize. Unoptimal,
            # but the only way to do it currently.
            body = json.loads(request.body)
            body.setdefault("meta", {})
            body["meta"]["type"] = (content_type.model_class() or Page)._meta.label
            request._body = json.dumps(body).encode()

        return func(request, *args, **kwargs)

    return wrapper


IntPKFilter: TypeAlias = PositiveInt
RootRelativeFilter: TypeAlias = IntPKFilter | Literal["root"]


# A no-op so that Ninja does not try to do a default exact lookup with the value
def custom_filter(self, value):
    return Q()


class PageFilterSchema(FilterSchema):
    type: list[PageTypeLiteral] = []
    ancestor_of: Optional[IntPKFilter] = None
    child_of: Optional[RootRelativeFilter] = None
    descendant_of: Optional[RootRelativeFilter] = None
    translation_of: Optional[RootRelativeFilter] = None
    locale: Annotated[Optional[str], FilterLookup("locale__language_code")] = None
    site: Optional[str] = None

    @field_validator("type", mode="after")
    @classmethod
    def parse_type(cls, value: list[PageTypeLiteral]) -> list:
        return [resolve_model_string(model) for model in value]

    def filter_type(self, value: list) -> Q:
        if len(value) <= 1:
            return Q()
        content_types = [
            ct.pk for ct in ContentType.objects.get_for_models(*value).values()
        ]
        return Q(content_type__in=content_types)

    @model_validator(mode="after")
    def validate_child_of_or_descendant_of(self):
        if self.child_of and self.descendant_of:
            raise ValueError(
                "filtering by descendant_of with child_of is not supported."
            )
        return self

    filter_ancestor_of = custom_filter
    filter_child_of = custom_filter
    filter_descendant_of = custom_filter
    filter_translation_of = custom_filter
    filter_site = custom_filter  # Handled via get_public_pages_queryset

    @staticmethod
    def get_request_root_page(request: HttpRequest) -> Page:
        return Site.find_for_request(request).root_page

    @staticmethod
    def get_public_page(request: HttpRequest, page_id: int) -> Page:
        return get_object_or_404(_public_pages_queryset(request), pk=page_id)

    @staticmethod
    def get_public_page_or_root(
        request: HttpRequest,
        page_id: RootRelativeFilter,
    ) -> Page:
        if page_id == "root":
            return PageFilterSchema.get_request_root_page(request)
        return PageFilterSchema.get_public_page(request, page_id)

    def apply_ancestor_of(
        self,
        request: HttpRequest,
        queryset: PageQuerySet,
    ) -> PageQuerySet:
        if self.ancestor_of is None:
            return queryset
        relative_to = self.get_public_page(request, self.ancestor_of)
        return queryset.ancestor_of(relative_to)

    def apply_descendant_of(
        self,
        request: HttpRequest,
        queryset: PageQuerySet,
    ) -> PageQuerySet:
        relative_to = self.child_of or self.descendant_of
        if relative_to is None:
            return queryset
        relative_to = self.get_public_page_or_root(request, relative_to)
        if self.child_of:
            return queryset.child_of(relative_to)
        return queryset.descendant_of(relative_to)

    def apply_translation_of(
        self,
        request: HttpRequest,
        queryset: PageQuerySet,
    ) -> PageQuerySet:
        if self.translation_of is None:
            return queryset
        relative_to = self.get_public_page_or_root(request, self.translation_of)
        return queryset.translation_of(relative_to)

    def apply_custom_filters(
        self,
        request: HttpRequest,
        queryset: PageQuerySet,
    ) -> PageQuerySet:
        queryset = self.apply_ancestor_of(request, queryset)
        queryset = self.apply_descendant_of(request, queryset)
        queryset = self.apply_translation_of(request, queryset)
        return queryset

    def filter(
        self,
        queryset: PageQuerySet,
        request: Optional[HttpRequest] = None,
    ) -> PageQuerySet:
        queryset = super().filter(queryset)
        # request is optional as it's not part of Ninja's FilterSchema API
        if request:
            queryset = self.apply_custom_filters(request, queryset)
        return queryset


class OrderingSchema(Schema):
    # Ninja query params always result in a list if the union type has a list,
    # but we use "random" literal (not ["random"]) for better OpenAPI spec.
    order: Literal["random"] | list[str] = []

    def order_queryset(
        self,
        queryset: QuerySet,
        pagination_info: WagtailLimitOffsetPagination.Input,
    ) -> QuerySet:
        validated_fields = OrderingValidator(
            model=queryset.model,
            fields=self.order,
            base_fields=BASE_PAGE_READ_FIELDS,
            db_fields_only=True,
            has_offset=bool(pagination_info.offset),
        )
        if validated_fields.fields:
            return queryset.order_by(*validated_fields.fields)
        return queryset


@router.get(
    "/",
    response=list[BasePageSchema],
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
    filters: PageFilterSchema = Query(...),  # ty: ignore[call-non-callable]
    ordering: OrderingSchema = Query(...),  # ty: ignore[call-non-callable]
    **kwargs,
):
    pagination_info = cast(
        WagtailLimitOffsetPagination.Input,
        kwargs.get("pagination_info"),
    )
    models = cast(list[type[Model]], filters.type)
    model = models[0] if len(models) == 1 else Page
    queryset = _public_pages_queryset(request, model)
    queryset = filters.filter(queryset, request)
    queryset = ordering.order_queryset(queryset, pagination_info)
    return queryset


@router.get(
    "/find/",
    response=PageDetailSchema,
    url_name="find_page",
    summary="Find page",
    operation_id="pages_find",
)
def find_page(
    request: HttpRequest,
    id: Optional[PositiveInt] = None,
    html_path: Optional[str] = None,
    site: Optional[str] = None,  # processed via get_public_pages_queryset
):
    page = None

    if html_path and (site := Site.find_for_request(request)):
        path_components = [component for component in html_path.split("/") if component]
        try:
            page, _, _ = site.root_page.specific.route(request, path_components)
        except Http404:
            page = None
        else:
            if not _public_pages_queryset(request).filter(id=page.id).exists():
                page = None

    if page is None and id:
        page = get_object_or_404(_public_pages_queryset(request), pk=id)

    if page is None:
        raise Http404("No Page matches the given query.")

    url = reverse("wagtailapi_v3:detail_page", kwargs={"page_id": page.pk})
    query = request.GET.copy()
    query.pop("id", None)
    query.pop("html_path", None)
    return redirect(f"{url}?{query.urlencode()}")


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


@router.post(
    "/",
    response={201: PageDetailSchema},
    url_name="create_page",
    summary="Create page",
    operation_id="pages_create",
)
@require_any_permission(Page, ("add",))
def create_page(request: HttpRequest, data: PageCreateSchema = Body(...)):  # ty: ignore[call-non-callable]
    model = resolve_model_string(data.meta.type)
    parent = get_object_or_404(Page, id=data.meta.parent_id).specific
    form = build_page_form(model, parent, data, request.user)
    action = CreatePageAction(
        form.instance,
        parent,
        user=request.user,
        form=form,
        publish=data.meta.action == "publish",
    )
    action.execute()
    return Status(201, form.instance)


@router.patch(
    "/{page_id}/",
    response=PageDetailSchema,
    url_name="update_page",
    summary="Update page",
    operation_id="pages_update",
)
@require_any_permission(Page, ("change",))
@decorate_view(default_meta_type)
def update_page(
    request: HttpRequest,
    page_id: int,
    data: PageUpdateSchema = Body(...),  # ty: ignore[call-non-callable]
):
    model = resolve_model_string(data.meta.type)
    page = get_object_or_404(model, pk=page_id)
    form = build_page_update_form(page, data, request.user)
    action = EditPageAction(
        form.instance,
        user=request.user,
        form=form,
        publish=data.meta.action == "publish",
    )
    action.execute()
    return form.instance
