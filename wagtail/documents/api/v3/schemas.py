from typing import Literal, cast

from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from ninja import Schema

from wagtail.api.v2.utils import get_full_url
from wagtail.api.v3.schemas import create_generator, patch_generator, read_generator
from wagtail.api.v3.schemas.base import BaseMetaSchema, BaseSchema
from wagtail.documents import get_document_model
from wagtail.models import Collection

Document = get_document_model()
BASE_DOCUMENT_FIELDS = [
    name for name in Document.admin_form_fields if name not in {"file", "tags"}
]
CollectionForeignKeySchema = read_generator.get_foreign_key_schema(Collection)


class DocumentMetaSchema(BaseMetaSchema):
    detail_url: str | None = None
    tags: list[str] = []
    download_url: str | None = None

    @staticmethod
    def resolve_detail_url(obj, context: dict) -> str | None:
        request = context["request"]
        try:
            path = reverse(
                "wagtailapi_v3:detail_document",
                kwargs={"document_id": obj.pk},
            )
            return get_full_url(request, path)
        except NoReverseMatch:
            return None

    @staticmethod
    def resolve_tags(obj) -> list[str]:
        return [tag.name for tag in obj.tags.all()]

    @staticmethod
    def resolve_download_url(obj, context: dict) -> str | None:
        if not obj.file:
            return None
        return get_full_url(context["request"], obj.url)


class DocumentSchema(BaseSchema):
    id: int
    title: str
    collection: CollectionForeignKeySchema  # ty: ignore[invalid-type-form]
    meta: DocumentMetaSchema


def _narrowed_document_meta_schema() -> type[Schema]:
    return cast(
        type[Schema],
        type(DocumentMetaSchema)(
            "DocumentDetailMetaSchema",
            (DocumentMetaSchema,),
            {"__annotations__": {"type": Literal[Document._meta.label]}},  # ty: ignore[invalid-type-form]
        ),
    )


def build_document_schemas():
    read_schema = read_generator.generate_schema(Document, base_class=DocumentSchema)
    read_schema = read_generator.extend_schema(
        read_schema,
        "DocumentSchema",
        {"meta": (_narrowed_document_meta_schema(), ..., None)},
    )
    create_schema = create_generator.generate_schema(
        Document,
        base_class=Schema,
        fields=BASE_DOCUMENT_FIELDS,
        required_fields=("title",),
    )
    patch_schema = patch_generator.generate_schema(
        Document,
        base_class=Schema,
        fields=BASE_DOCUMENT_FIELDS,
    )
    return read_schema, create_schema, patch_schema
