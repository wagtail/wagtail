from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router, Status
from ninja.pagination import paginate

from wagtail.actions.create import CreateAction
from wagtail.actions.delete import DeleteAction
from wagtail.actions.edit import EditAction
from wagtail.api.v3.pagination import WagtailLimitOffsetPagination
from wagtail.api.v3.permissions import require_any_permission
from wagtail.api.v3.schemas import SiteInputSchema, SiteSchema
from wagtail.models import Site
from wagtail.permissions import site_permission_policy
from wagtail.sites.forms import SiteForm

router = Router(tags=["sites"])


@router.get(
    "/",
    response=list[SiteSchema],
    url_name="list_sites",
    summary="List sites",
    operation_id="sites_list",
)
@paginate(WagtailLimitOffsetPagination)
@require_any_permission(Site)
def list_sites(request: HttpRequest):
    return site_permission_policy.instances_user_has_any_permission_for(
        request.user,
        ("add", "change", "delete", "view"),
    )


@router.get(
    "/{site_id}/",
    response=SiteSchema,
    url_name="detail_site",
    summary="Site detail",
    operation_id="sites_detail",
)
@require_any_permission(Site)
def get_site(request: HttpRequest, site_id: int):
    return get_object_or_404(
        site_permission_policy.instances_user_has_any_permission_for(
            request.user,
            ("add", "change", "delete", "view"),
        ),
        pk=site_id,
    )


@router.post(
    "/",
    response={201: SiteSchema},
    url_name="create_site",
    summary="Create site",
    operation_id="sites_create",
)
@require_any_permission(Site, ("add",))
def create_site(request: HttpRequest, data: SiteInputSchema):
    form = SiteForm(data.dict())
    CreateAction(form.instance, user=request.user, form=form).execute(
        skip_permission_checks=True
    )
    return Status(201, form.instance)


@router.put(
    "/{site_id}/",
    response=SiteSchema,
    url_name="update_site",
    summary="Update site",
    operation_id="sites_update",
)
def update_site(request: HttpRequest, site_id: int, data: SiteInputSchema):
    site = get_object_or_404(Site, pk=site_id)
    form = SiteForm(data.dict(), instance=site)
    EditAction(form.instance, user=request.user, form=form).execute()
    return form.instance


@router.delete(
    "/{site_id}/",
    response={204: None},
    url_name="delete_site",
    summary="Delete site",
    operation_id="sites_delete",
)
def delete_site(request: HttpRequest, site_id: int):
    site = get_object_or_404(Site, pk=site_id)
    DeleteAction(site, user=request.user).execute()
    return Status(204, None)
