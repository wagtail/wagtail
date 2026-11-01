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
from wagtail.documents import get_document_model

from .form_data import build_document_form, build_document_update_form

router = Router(tags=["documents"])
Document = get_document_model()
registered_schemas = cast(ContentTypeRegistration, registry.get(Document._meta.label))
DocumentDetailSchema = cast(type[BaseModel], registered_schemas.read_schema)
DocumentCreateSchema = cast(type[BaseModel], registered_schemas.create_schema)
DocumentPatchSchema = cast(type[BaseModel], registered_schemas.patch_schema)
BASE_DOCUMENT_READ_FIELDS = ["id", "title"]


def get_documents_queryset(request: HttpRequest):
    restricted_collection_ids = get_restricted_collection_ids(request)
    return (
        Document.objects.exclude(collection__in=restricted_collection_ids)
        .prefetch_related("tags")
        .order_by("id")
    )


@router.get(
    "/",
    response=list[DocumentDetailSchema],  # ty: ignore[invalid-type-form]
    url_name="list_documents",
    summary="List documents",
    operation_id="documents_list",
    auth=[BearerTokenAuth(), AllowAnonymous()],
)
@paginate(
    WagtailLimitOffsetPagination,
    pass_parameter="pagination_info",  # noqa: S106 not a password
)
def list_documents(
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
        base_fields=BASE_DOCUMENT_READ_FIELDS,
    )
    queryset = get_documents_queryset(request)
    queryset = field_filter.filter_queryset(queryset)
    queryset = ordering.order_queryset(
        queryset,
        pagination_info,
        base_fields=BASE_DOCUMENT_READ_FIELDS,
    )
    queryset = search.search_queryset(request, queryset)
    return queryset


@router.get(
    "/{document_id}/",
    response=DocumentDetailSchema,
    url_name="detail_document",
    summary="Document detail",
    operation_id="documents_detail",
    auth=[BearerTokenAuth(), AllowAnonymous()],
)
def get_document(request: HttpRequest, document_id: int):
    return get_object_or_404(get_documents_queryset(request), pk=document_id)


@router.post(
    "/",
    response={201: DocumentDetailSchema},
    url_name="create_document",
    summary="Create document",
    operation_id="documents_create",
    auth=BearerTokenAuth(),
)
@require_any_permission(Document, ("add",))
def create_document(
    request: HttpRequest,
    file: UploadedFile = File(...),  # ty: ignore[call-non-callable]
    data: DocumentCreateSchema = Form(...),  # ty: ignore[call-non-callable, invalid-type-form]
):
    form = build_document_form(Document, data, file, request.user)
    action_class = action_registry.get_action_class(Document, "create")
    action = action_class(form.instance, user=request.user, form=form)
    action.execute()
    return Status(201, form.instance)


@router.patch(
    "/{document_id}/",
    response=DocumentDetailSchema,
    url_name="update_document",
    summary="Update document",
    operation_id="documents_update",
    auth=BearerTokenAuth(),
)
@require_any_permission(Document, ("change",))
def update_document(
    request: HttpRequest,
    document_id: int,
    data: DocumentPatchSchema = Body(...),  # ty: ignore[call-non-callable, invalid-type-form]
):
    document = get_object_or_404(Document, pk=document_id)
    form = build_document_update_form(document, data, request.user)
    action_class = action_registry.get_action_class(Document, "edit")
    action = action_class(form.instance, user=request.user, form=form)
    action.execute()
    return form.instance


@router.delete(
    "/{document_id}/",
    response={204: None},
    url_name="delete_document",
    summary="Delete document",
    operation_id="documents_delete",
    auth=BearerTokenAuth(),
)
@require_any_permission(Document, ("delete",))
def delete_document(request: HttpRequest, document_id: int):
    document = get_object_or_404(Document, pk=document_id)
    action_class = action_registry.get_action_class(Document, "delete")
    action = action_class(document, user=request.user)
    action.execute()
    return Status(204, None)
