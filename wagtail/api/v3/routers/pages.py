from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Body, Router, Status
from ninja.pagination import paginate

from wagtail.actions.create_page import CreatePageAction
from wagtail.actions.edit_page import EditPageAction
from wagtail.api.v3.form_data import build_page_form, build_page_update_form
from wagtail.api.v3.pagination import WagtailLimitOffsetPagination
from wagtail.api.v3.permissions import require_any_permission
from wagtail.api.v3.querysets import AccessTier, get_pages_queryset
from wagtail.api.v3.schemas import BasePageSchema
from wagtail.api.v3.schemas.base import build_union_schemas
from wagtail.coreutils import resolve_model_string
from wagtail.models import Page, get_page_models
from wagtail.utils.forms import FormValidationError

router = Router(tags=["pages"])


_page_schemas = build_union_schemas(get_page_models())
PageDetailSchema = _page_schemas.detail
PageCreateSchema = _page_schemas.create
PageUpdateSchema = _page_schemas.update


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
