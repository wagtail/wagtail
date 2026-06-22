from typing import Any

from django.http import Http404, HttpRequest
from ninja import Router, Schema

from wagtail.api.v3.registry import get_type_schemas, list_content_types
from wagtail.api.v3.schemas import ContentTypeSummarySchema

router = Router(tags=["schema"])


class ContentTypeListSchema(Schema):
    types: list[ContentTypeSummarySchema]


class SchemaDetailResponse(Schema):
    read: dict[str, Any] | None = None
    create: dict[str, Any] | None = None
    patch: dict[str, Any] | None = None


@router.get(
    "/",
    response=ContentTypeListSchema,
    url_name="list_schemas",
    summary="List registered content types",
    operation_id="schema_list",
)
def list_schemas(request: HttpRequest):
    return {"types": list_content_types()}


@router.get(
    "/{type_name}/",
    response=SchemaDetailResponse,
    url_name="get_schema_for_type",
    summary="Schemas for a content type",
    operation_id="schema_detail",
)
def get_schema_for_type(request: HttpRequest, type_name: str):
    schemas = get_type_schemas(type_name)
    if schemas is None:
        raise Http404(f"Unknown content type: {type_name}")
    return schemas
