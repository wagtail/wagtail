from wagtail.api.v3.registry import ContentTypeRegistration, registry
from wagtail.documents import get_document_model

from .schemas import build_document_schemas


def register_content_types() -> None:
    Document = get_document_model()
    read_schema, create_schema, patch_schema = build_document_schemas()
    registry.register(
        ContentTypeRegistration(
            name=Document._meta.label,
            label=str(Document._meta.verbose_name),
            read_schema=read_schema,
            create_schema=create_schema,
            patch_schema=patch_schema,
        )
    )
