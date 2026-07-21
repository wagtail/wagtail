from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Body, Router, Status
from ninja.pagination import paginate

from wagtail.actions.create_page import CreatePageAction
from wagtail.api.v3.builders import build_page_form
from wagtail.api.v3.pagination import WagtailLimitOffsetPagination
from wagtail.api.v3.permissions import require_any_permission
from wagtail.api.v3.querysets import AccessTier, get_pages_queryset
from wagtail.api.v3.schemas import (
    BasePageSchema,
    build_page_input_schema_union,
    build_page_schema_union,
)
from wagtail.coreutils import resolve_model_string
from wagtail.models import Page, get_page_models
from wagtail.utils.forms import FormValidationError

router = Router(tags=["pages"])

#: A discriminated union of every concrete page model's generated schema,
#: so the detail endpoint's response accurately reflects whichever specific
#: page type was requested, instead of only the fields BasePageSchema has.
PageDetailSchema = build_page_schema_union(get_page_models())

#: A discriminated union of every concrete page model's generated input
#: schema, so the create endpoint accepts whichever fields are valid for the
#: specific page type named by its "type" field.
PageCreateSchema = build_page_input_schema_union(get_page_models())


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
            {("meta", "type"): [f"Unknown page type: {data.meta.type!r}"]}
        )
    parent = get_object_or_404(Page.objects.all(), pk=data.meta.parent_id).specific
    form = build_page_form(model, parent, data, request.user)
    action = CreatePageAction(
        form.instance,
        parent,
        user=request.user,
        form=form,
        clean=True,
    )
    action.execute()
    return Status(201, form.instance)
