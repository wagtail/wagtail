from wagtail.api.v3.registry import ContentTypeRegistration, registry
from wagtail.images import get_image_model

from .schemas import build_image_schemas


def register_content_types() -> None:
    """Register the active image model's read/create/patch schemas."""
    Image = get_image_model()
    read_schema, create_schema, patch_schema = build_image_schemas()
    registry.register(
        ContentTypeRegistration(
            name=Image._meta.label,
            label=str(Image._meta.verbose_name),
            read_schema=read_schema,
            create_schema=create_schema,
            patch_schema=patch_schema,
        )
    )
