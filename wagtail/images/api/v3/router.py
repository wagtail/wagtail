from typing import cast

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Body, File, Form, Query, Router, Status, UploadedFile
from ninja.pagination import paginate
from pydantic import BaseModel

from wagtail.actions import action_registry
from wagtail.api.v3.auth import AllowAnonymous, BearerTokenAuth
from wagtail.api.v3.pagination import WagtailLimitOffsetPagination
from wagtail.api.v3.permissions import (
    get_restricted_collection_ids,
    require_any_permission,
)
from wagtail.api.v3.registry import ContentTypeRegistration, registry
from wagtail.api.v3.schemas.params import (
    APIFieldFilterSchema,
    OrderingSchema,
    SearchSchema,
)
from wagtail.images import get_image_model

from .form_data import build_image_form, build_image_update_form

router = Router(tags=["images"])

Image = get_image_model()
registered_schemas = cast(ContentTypeRegistration, registry.get(Image._meta.label))
ImageDetailSchema = cast(type[BaseModel], registered_schemas.read_schema)
ImageCreateSchema = cast(type[BaseModel], registered_schemas.create_schema)
ImagePatchSchema = cast(type[BaseModel], registered_schemas.patch_schema)

#: Fields every image listing can be filtered/ordered by, beyond the model's
#: own ``api_fields``.
BASE_IMAGE_READ_FIELDS = ["id", "title", "width", "height"]


def get_images_queryset(request: HttpRequest):
    """v2-parity public queryset: images not in restricted collections."""
    restricted_collection_ids = get_restricted_collection_ids(request)
    return (
        Image.objects.exclude(collection__in=restricted_collection_ids)
        .prefetch_related("tags")
        .order_by("id")
    )


@router.get(
    "/",
    response=list[ImageDetailSchema],  # ty: ignore[invalid-type-form]
    url_name="list_images",
    summary="List images",
    operation_id="images_list",
    auth=[BearerTokenAuth(), AllowAnonymous()],
)
@paginate(
    WagtailLimitOffsetPagination,
    pass_parameter="pagination_info",  # noqa: S106 not a password
)
def list_images(
    request: HttpRequest,
    ordering: OrderingSchema = Query(...),  # ty: ignore[call-non-callable]
    search: SearchSchema = Query(...),  # ty: ignore[call-non-callable]
    **kwargs,
):
    pagination_info = cast(
        WagtailLimitOffsetPagination.Input,
        kwargs.get("pagination_info"),
    )
    field_filter = APIFieldFilterSchema.with_exclude_schemas(
        raw_params=request.GET,
        schemas=(OrderingSchema, SearchSchema),
        base_fields=BASE_IMAGE_READ_FIELDS,
    )
    queryset = get_images_queryset(request)
    queryset = field_filter.filter_queryset(queryset)
    queryset = ordering.order_queryset(
        queryset, pagination_info, base_fields=BASE_IMAGE_READ_FIELDS
    )
    queryset = search.search_queryset(request, queryset)
    return queryset


@router.get(
    "/{image_id}/",
    response=ImageDetailSchema,
    url_name="detail_image",
    summary="Image detail",
    operation_id="images_detail",
    auth=[BearerTokenAuth(), AllowAnonymous()],
)
def get_image(request: HttpRequest, image_id: int):
    return get_object_or_404(get_images_queryset(request), pk=image_id)


@router.post(
    "/",
    response={201: ImageDetailSchema},
    url_name="create_image",
    summary="Create image",
    operation_id="images_create",
    auth=BearerTokenAuth(),
)
@require_any_permission(Image, ("add",))
def create_image(
    request: HttpRequest,
    file: UploadedFile = File(...),  # ty: ignore[call-non-callable]
    data: ImageCreateSchema = Form(...),  # ty: ignore[call-non-callable, invalid-type-form]
):
    form = build_image_form(Image, data, file, request.user)
    action_class = action_registry.get_action_class(Image, "create")
    action = action_class(form.instance, user=request.user, form=form)
    action.execute()
    return Status(201, form.instance)


@router.patch(
    "/{image_id}/",
    response=ImageDetailSchema,
    url_name="update_image",
    summary="Update image",
    operation_id="images_update",
    auth=BearerTokenAuth(),
)
@require_any_permission(Image, ("change",))
def update_image(
    request: HttpRequest,
    image_id: int,
    data: ImagePatchSchema = Body(...),  # ty: ignore[call-non-callable, invalid-type-form]
):
    image = get_object_or_404(Image, pk=image_id)
    form = build_image_update_form(image, data, request.user)
    action_class = action_registry.get_action_class(Image, "edit")
    action = action_class(form.instance, user=request.user, form=form)
    action.execute()
    return form.instance


@router.delete(
    "/{image_id}/",
    response={204: None},
    url_name="delete_image",
    summary="Delete image",
    operation_id="images_delete",
    auth=BearerTokenAuth(),
)
@require_any_permission(Image, ("delete",))
def delete_image(request: HttpRequest, image_id: int):
    image = get_object_or_404(Image, pk=image_id)
    action_class = action_registry.get_action_class(Image, "delete")
    action = action_class(image, user=request.user)
    action.execute()
    return Status(204, None)
