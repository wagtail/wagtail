from typing import Literal, cast

from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from ninja import Schema

from wagtail.api.v2.utils import get_full_url
from wagtail.api.v3.schemas import create_generator, patch_generator, read_generator
from wagtail.api.v3.schemas.base import BaseMetaSchema, BaseSchema
from wagtail.images import get_image_model
from wagtail.models import Collection

Image = get_image_model()

#: Image's own writable fields exposed on create/update, beyond whatever
#: extra fields a model declares through ``api_fields``. Mirrors
#: ``Image.admin_form_fields`` minus fields not writable through the API:
#: ``file`` is uploaded separately on create and is not replaceable in 8.0,
#: while tags remain read-only until shared tag writing support is introduced.
BASE_IMAGE_FIELDS = [
    name for name in Image.admin_form_fields if name not in {"file", "tags"}
]

#: Standard v3 foreign-key shape (``{id, meta: {type}}``) for the collection field.
CollectionForeignKeySchema = read_generator.get_foreign_key_schema(Collection)


class ImageMetaSchema(BaseMetaSchema):
    detail_url: str | None = None
    tags: list[str] = []
    download_url: str | None = None

    @staticmethod
    def resolve_detail_url(obj, context: dict) -> str | None:
        request = context["request"]
        try:
            path = reverse("wagtailapi_v3:detail_image", kwargs={"image_id": obj.pk})
            return get_full_url(request, path)
        except NoReverseMatch:
            return None

    @staticmethod
    def resolve_tags(obj) -> list[str]:
        # Iterate .all() rather than values_list: the listing queryset
        # prefetches tags, and values_list clones the queryset, bypassing
        # the prefetch cache (one query per image). .all() uses the cache.
        return [tag.name for tag in obj.tags.all()]

    @staticmethod
    def resolve_download_url(obj) -> str | None:
        return obj.file.url if obj.file else None


class ImageSchema(BaseSchema):
    """Read schema for an image: v2 parity fields plus the writable set."""

    id: int
    title: str
    width: int
    height: int
    description: str | None = None
    collection: CollectionForeignKeySchema  # ty: ignore[invalid-type-form]
    focal_point_x: int | None = None
    focal_point_y: int | None = None
    focal_point_width: int | None = None
    focal_point_height: int | None = None
    meta: ImageMetaSchema


def _narrowed_image_meta_schema() -> type[Schema]:
    """Narrow the read meta's ``type`` to the active image model's label under
    a distinct class name, so the OpenAPI component doesn't collide with the
    FK-narrowed ``ImageMetaSchema`` already emitted for foreign keys to Image
    (ninja keys components by class ``__name__``)."""
    return cast(
        type[Schema],
        type(ImageMetaSchema)(
            "ImageDetailMetaSchema",
            (ImageMetaSchema,),
            {"__annotations__": {"type": Literal[Image._meta.label]}},  # ty: ignore[invalid-type-form]
        ),
    )


def build_image_schemas():
    """Build the read/create/patch schemas for the active image model."""
    read_schema = read_generator.generate_schema(Image, base_class=ImageSchema)
    read_schema = read_generator.extend_schema(
        read_schema,
        "ImageSchema",
        {"meta": (_narrowed_image_meta_schema(), ..., None)},
    )
    create_schema = create_generator.generate_schema(
        Image,
        base_class=Schema,
        fields=BASE_IMAGE_FIELDS,
        required_fields=("title",),
    )
    patch_schema = patch_generator.generate_schema(
        Image,
        base_class=Schema,
        fields=BASE_IMAGE_FIELDS,
    )
    return read_schema, create_schema, patch_schema
