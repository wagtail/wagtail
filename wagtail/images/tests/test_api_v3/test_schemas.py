from django.urls import reverse

from wagtail.api.v3.registry import registry
from wagtail.images import get_image_model

from .base import TestV3ImagesBase


class TestV3ImageSchemas(TestV3ImagesBase):
    def setUp(self):
        super().setUp()
        self.Image = get_image_model()
        self.registration = registry.get(self.Image._meta.label)

    def test_content_type_registered_for_schema_discovery(self):
        self.assertIsNotNone(self.registration)
        schemas = registry.get_type_schemas(self.Image._meta.label)
        self.assertIn("read", schemas)
        self.assertIn("create", schemas)
        self.assertIn("patch", schemas)

    def test_read_schema_shape(self):
        schema = self.registration.read_schema
        properties = schema.model_json_schema()["properties"]
        # v2 parity fields plus the writable set (every writable field readable).
        for field in (
            "id",
            "title",
            "width",
            "height",
            "description",
            "collection",
            "focal_point_x",
        ):
            self.assertIn(field, properties)
        self.assertIn("meta", properties)

    def test_read_meta_has_distinct_component_name(self):
        # The read meta must not collide with the FK-narrowed ImageMetaSchema
        # already emitted for foreign keys to Image (ninja keys OpenAPI
        # components by class __name__).
        meta = self.registration.read_schema.model_fields["meta"].annotation
        self.assertEqual(meta.__name__, "ImageDetailMetaSchema")

    def test_read_meta_fields(self):
        meta = self.registration.read_schema.model_fields["meta"]
        meta_schema = meta.annotation.model_json_schema()["properties"]
        for field in ("type", "detail_url", "tags", "download_url"):
            self.assertIn(field, meta_schema)

    def test_create_schema_has_admin_form_fields(self):
        properties = self.registration.create_schema.model_json_schema()["properties"]
        for name in ("title", "description", "collection_id", "focal_point_x"):
            self.assertIn(name, properties)
        # The file is uploaded separately; tags remain read-only for now.
        self.assertNotIn("file", properties)

    def test_write_schemas_exclude_tags(self):
        self.assertNotIn("tags", self.registration.create_schema.model_fields)
        self.assertNotIn("tags", self.registration.patch_schema.model_fields)

    def test_patch_schema_fields_optional(self):
        schema = self.registration.patch_schema
        for name, field in schema.model_fields.items():
            if name == "meta":
                continue
            self.assertFalse(field.is_required(), f"{name} should be optional")

    def test_schema_discovery_endpoint_lists_images(self):
        self.login()
        response = self.client.get(reverse("wagtailapi_v3:list_schemas"))
        names = [entry["name"] for entry in response.json()["types"]]
        self.assertIn(self.Image._meta.label, names)
