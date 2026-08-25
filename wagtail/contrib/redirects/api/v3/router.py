from datetime import datetime
from typing import Optional, cast

from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from ninja import Field, Query, Router, Schema, Status
from ninja.pagination import paginate

from wagtail.actions import action_registry
from wagtail.api.v3.auth import AllowAnonymous, BearerTokenAuth
from wagtail.api.v3.pagination import WagtailLimitOffsetPagination
from wagtail.api.v3.permissions import require_any_permission
from wagtail.api.v3.schemas.params import APIFieldFilterSchema, OrderingSchema
from wagtail.contrib.redirects.forms import RedirectForm
from wagtail.contrib.redirects.middleware import get_redirect
from wagtail.contrib.redirects.models import Redirect

BASE_REDIRECT_READ_FIELDS = [
    "id",
    "old_path",
    "site",
    "is_permanent",
    "redirect_page",
    "redirect_page_route_path",
    "automatically_created",
    "created_at",
]

# All redirects endpoints require a bearer token; see wagtail.api.v3.auth.
router = Router(tags=["redirects"], auth=BearerTokenAuth())


class RedirectSchema(Schema):
    id: int
    old_path: str
    site_id: int | None
    is_permanent: bool
    redirect_page_id: int | None
    redirect_page_route_path: str
    redirect_link: str
    automatically_created: bool
    created_at: datetime | None


class RedirectInputSchema(Schema):
    old_path: str
    site: int | None = None
    is_permanent: bool = True
    # Accept redirect_page_id in the input schema for consistency with the output,
    # but use redirect_page so it can be accepted by ModelForm.
    redirect_page: int | None = Field(None, alias="redirect_page_id")
    redirect_page_route_path: str = ""
    redirect_link: str = ""


@router.get(
    "/",
    response=list[RedirectSchema],
    url_name="list_redirects",
    summary="List redirects",
    operation_id="redirects_list",
    # v2 parity: redirects are public data (the redirect middleware resolves
    # them publicly), so reads allow anonymous access like the v2 API.
    auth=[BearerTokenAuth(), AllowAnonymous()],
)
@paginate(
    WagtailLimitOffsetPagination,
    pass_parameter="pagination_info",  # noqa: S106 not a password
)
def list_redirects(
    request: HttpRequest,
    ordering: OrderingSchema = Query(...),  # ty: ignore[call-non-callable]
    **kwargs,
):
    pagination_info = cast(
        WagtailLimitOffsetPagination.Input,
        kwargs.get("pagination_info"),
    )
    field_filter = APIFieldFilterSchema.with_exclude_schemas(
        raw_params=request.GET,
        schemas=(OrderingSchema,),
        base_fields=BASE_REDIRECT_READ_FIELDS,
    )
    queryset = Redirect.objects.all()
    queryset = field_filter.filter_queryset(queryset)
    queryset = ordering.order_queryset(
        queryset,
        pagination_info,
        base_fields=BASE_REDIRECT_READ_FIELDS,
    )
    return queryset


@router.get(
    "/find/",
    response=RedirectSchema,
    url_name="find_redirect",
    summary="Find redirect",
    operation_id="redirects_find",
    # Public read, like the list view and the v2 API.
    auth=[BearerTokenAuth(), AllowAnonymous()],
)
def find_redirect(
    request: HttpRequest,
    id: Optional[int] = None,
    html_path: Optional[str] = None,
):
    redirect_obj = None

    if html_path:
        redirect_obj = get_redirect(request, html_path)

    if redirect_obj is None and id:
        redirect_obj = get_object_or_404(Redirect, pk=id)

    if redirect_obj is None:
        raise Http404(f"No {Redirect._meta.object_name} matches the given query.")

    url = reverse(
        "wagtailapi_v3:detail_redirect",
        kwargs={"redirect_id": redirect_obj.pk},
    )
    query = request.GET.copy()
    query.pop("id", None)
    query.pop("html_path", None)
    return redirect(f"{url}?{query.urlencode()}")


@router.get(
    "/{redirect_id}/",
    response=RedirectSchema,
    url_name="detail_redirect",
    summary="Redirect detail",
    operation_id="redirects_detail",
    # Public read, like the list view and the v2 API.
    auth=[BearerTokenAuth(), AllowAnonymous()],
)
def get_redirect_detail(request: HttpRequest, redirect_id: int):
    return get_object_or_404(Redirect, pk=redirect_id)


@router.post(
    "/",
    response={201: RedirectSchema},
    url_name="create_redirect",
    summary="Create redirect",
    operation_id="redirects_create",
)
@require_any_permission(Redirect, ("add",))
def create_redirect(request: HttpRequest, data: RedirectInputSchema):
    form = RedirectForm(data.dict())
    action_class = action_registry.get_action_class(Redirect, "create")
    action_class(form.instance, user=request.user, form=form).execute(
        skip_permission_checks=True
    )
    return Status(201, form.instance)


@router.put(
    "/{redirect_id}/",
    response=RedirectSchema,
    url_name="update_redirect",
    summary="Update redirect",
    operation_id="redirects_update",
)
@require_any_permission(Redirect, ("change",))
def update_redirect(request: HttpRequest, redirect_id: int, data: RedirectInputSchema):
    redirect = get_object_or_404(Redirect, pk=redirect_id)
    form = RedirectForm(data.dict(), instance=redirect)
    action_class = action_registry.get_action_class(Redirect, "edit")
    action_class(form.instance, user=request.user, form=form).execute()
    return form.instance


@router.delete(
    "/{redirect_id}/",
    response={204: None},
    url_name="delete_redirect",
    summary="Delete redirect",
    operation_id="redirects_delete",
)
@require_any_permission(Redirect, ("delete",))
def delete_redirect(request: HttpRequest, redirect_id: int):
    redirect = get_object_or_404(Redirect, pk=redirect_id)
    action_class = action_registry.get_action_class(Redirect, "delete")
    action_class(redirect, user=request.user).execute()
    return Status(204, None)
