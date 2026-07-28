import functools
import json
from typing import Literal, TypeAlias, cast

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Body, FilterSchema, Query, Router, Status
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
from wagtail.api.v3.schemas.pages import PageUpdateBaseSchema
from wagtail.coreutils import resolve_model_string
from wagtail.models import Page, Site, get_page_models
from wagtail.query import PageQuerySet
from wagtail.utils.forms import FormValidationError

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


IntPKFilter: TypeAlias = PositiveInt | None
DescendantOfFilter: TypeAlias = IntPKFilter | Literal["root"]


# A no-op so that Ninja does not try to do a default exact lookup with the value
def custom_filter(self, value):
    return Q()


class PageFilterSchema(FilterSchema):
    type: list[PageTypeLiteral] = []
    child_of: DescendantOfFilter = None
    descendant_of: DescendantOfFilter = None

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

    filter_child_of = custom_filter
    filter_descendant_of = custom_filter

    def apply_descendant_of(
        self,
        request: HttpRequest,
        queryset: PageQuerySet,
    ) -> PageQuerySet:
        relative_to = self.child_of or self.descendant_of
        if relative_to is None:
            return queryset
        if relative_to == "root":
            relative_to = Site.find_for_request(request).root_page
        else:
            relative_to = get_object_or_404(
                _public_pages_queryset(request, Page),
                pk=relative_to,
            )
        if self.child_of:
            return queryset.child_of(relative_to)
        return queryset.descendant_of(relative_to)


@router.get(
    "/",
    response=list[BasePageSchema],
    url_name="list_pages",
    summary="List pages",
    operation_id="pages_list",
)
@paginate(WagtailLimitOffsetPagination)
def list_pages(
    request: HttpRequest,
    filters: PageFilterSchema = Query(...),  # ty: ignore[call-non-callable]
):
    models = cast(list[type[Model]], filters.type)
    model = models[0] if len(models) == 1 else Page
    queryset = _public_pages_queryset(request, model)
    queryset = filters.filter(queryset)
    queryset = filters.apply_descendant_of(request, queryset)
    return queryset


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
    if not (model and issubclass(model, Page)):
        raise FormValidationError(
            {("meta", "type"): [(f"Unknown page type: {data.meta.type!r}", "invalid")]}
        )
    parent = get_object_or_404(Page.objects.all(), pk=data.meta.parent_id).specific
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
    page = get_object_or_404(Page.objects.all(), pk=page_id).specific
    if data.meta.type != type(page)._meta.label:
        raise FormValidationError(
            {
                ("meta", "type"): [
                    (
                        f"Page type cannot be changed: expected "
                        f"{type(page)._meta.label!r}, got {data.meta.type!r}",
                        "invalid",
                    )
                ]
            }
        )
    form = build_page_update_form(page, data, request.user)
    action = EditPageAction(
        form.instance,
        user=request.user,
        form=form,
        publish=data.meta.action == "publish",
    )
    action.execute()
    return form.instance
