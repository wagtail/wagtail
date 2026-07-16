from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Body, Router, Status
from ninja.pagination import paginate

from wagtail.actions.create import CreateAction
from wagtail.api.v3.builders import build_page_instance
from wagtail.api.v3.pagination import WagtailLimitOffsetPagination
from wagtail.api.v3.querysets import AccessTier, get_pages_queryset
from wagtail.api.v3.schemas import (
    BasePageSchema,
    build_page_input_schema_union,
    build_page_schema_union,
)
from wagtail.models import Page, get_page_models

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


def _get_page_model(type_label: str) -> type[Page]:
    for model in get_page_models():
        if model._meta.label == type_label:
            return model
    raise ValidationError({"type": f"Unknown page type: {type_label!r}"})


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
def create_page(request: HttpRequest, data: PageCreateSchema = Body(...)):  # ty: ignore[call-non-callable]
    if not request.user.is_active:
        raise PermissionDenied

    parent = get_object_or_404(Page.objects.all(), pk=data.parent_id).specific

    if not parent.permissions_for_user(request.user).can_add_subpage():
        raise PermissionDenied

    model = _get_page_model(data.type)
    if model not in parent.creatable_subpage_models() or not model.can_create_at(
        parent
    ):
        raise PermissionDenied

    page = build_page_instance(model, parent, data, request.user)
    page.live = False
    parent.add_child(instance=page)

    CreateAction(page, user=request.user, clean=False).execute(
        skip_permission_checks=True
    )
    return Status(201, page)
