from datetime import datetime

from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Field, Router, Schema, Status
from ninja.pagination import paginate
from rest_framework import serializers

from wagtail.actions.create import CreateAction
from wagtail.actions.delete import DeleteAction
from wagtail.actions.edit import EditAction
from wagtail.api.v2.filters import FieldsFilter, OrderingFilter, SearchFilter
from wagtail.api.v2.serializers import BaseSerializer
from wagtail.api.v2.views import BaseAPIViewSet
from wagtail.api.v3.pagination import WagtailLimitOffsetPagination
from wagtail.api.v3.permissions import require_any_permission
from wagtail.contrib.redirects.forms import RedirectForm
from wagtail.contrib.redirects.middleware import get_redirect
from wagtail.contrib.redirects.models import Redirect
from wagtail.contrib.redirects.permissions import permission_policy

router = Router(tags=["redirects"])


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
)
@paginate(WagtailLimitOffsetPagination)
@require_any_permission(Redirect)
def list_redirects(request: HttpRequest):
    return permission_policy.instances_user_has_any_permission_for(
        request.user,
        ("add", "change", "delete", "view"),
    )


@router.get(
    "/{redirect_id}/",
    response=RedirectSchema,
    url_name="detail_redirect",
    summary="Redirect detail",
    operation_id="redirects_detail",
)
@require_any_permission(Redirect)
def get_redirect_detail(request: HttpRequest, redirect_id: int):
    return get_object_or_404(
        permission_policy.instances_user_has_any_permission_for(
            request.user,
            ("add", "change", "delete", "view"),
        ),
        pk=redirect_id,
    )


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
    CreateAction(form.instance, user=request.user, form=form).execute(
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
def update_redirect(request: HttpRequest, redirect_id: int, data: RedirectInputSchema):
    redirect = get_object_or_404(Redirect, pk=redirect_id)
    form = RedirectForm(data.dict(), instance=redirect)
    EditAction(form.instance, user=request.user, form=form).execute()
    return form.instance


@router.delete(
    "/{redirect_id}/",
    response={204: None},
    url_name="delete_redirect",
    summary="Delete redirect",
    operation_id="redirects_delete",
)
def delete_redirect(request: HttpRequest, redirect_id: int):
    redirect = get_object_or_404(Redirect, pk=redirect_id)
    DeleteAction(redirect, user=request.user).execute()
    return Status(204, None)


# Legacy API v2


class RedirectSerializer(BaseSerializer):
    location = serializers.CharField(source="link")


class RedirectsAPIViewSet(BaseAPIViewSet):
    base_serializer_class = RedirectSerializer
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    body_fields = BaseAPIViewSet.body_fields + ["old_path", "location"]
    name = "redirects"
    model = Redirect

    listing_default_fields = BaseAPIViewSet.listing_default_fields + [
        "old_path",
        "location",
    ]

    def find_object(self, queryset, request):
        if "html_path" in request.GET:
            redirect = get_redirect(
                request,
                request.GET["html_path"],
            )

            if redirect is None:
                raise Http404
            else:
                return redirect

        return super().find_object(queryset, request)
