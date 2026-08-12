from wagtail.documents import get_document_model
from wagtail.documents.api.v3.schemas import build_document_schemas

from .base import TestV3DocumentsBase

Document = get_document_model()


class TestV3DocumentSchemas(TestV3DocumentsBase):
    def test_read_schema_shape(self):
        read_schema, _, _ = build_document_schemas()
        properties = read_schema.model_json_schema()["properties"]
        self.assertTrue({"id", "title", "collection", "meta"} <= properties.keys())

    def test_read_meta_fields(self):
        read_schema, _, _ = build_document_schemas()
        meta = read_schema.model_fields["meta"].annotation
        self.assertEqual(meta.__name__, "DocumentDetailMetaSchema")
        self.assertTrue(
            {"type", "detail_url", "tags", "download_url"}
            <= meta.model_json_schema()["properties"].keys()
        )

    def test_create_schema_fields(self):
        _, create_schema, _ = build_document_schemas()
        self.assertIn("title", create_schema.model_fields)
        self.assertIn("collection_id", create_schema.model_json_schema()["properties"])
        self.assertNotIn("file", create_schema.model_fields)
        self.assertNotIn("tags", create_schema.model_fields)
        self.assertTrue(create_schema.model_fields["title"].is_required())

    def test_patch_schema_fields_are_optional(self):
        _, _, patch_schema = build_document_schemas()
        self.assertNotIn("file", patch_schema.model_fields)
        self.assertNotIn("tags", patch_schema.model_fields)
        for field in patch_schema.model_fields.values():
            self.assertFalse(field.is_required())
