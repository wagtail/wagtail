from django.test import TestCase
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base

PAGE_READ_SCHEMA_FIELDS = {"id", "title", "meta"}
PAGE_READ_META_SCHEMA_FIELDS = {
    "type",
    "detail_url",
    "html_url",
    "slug",
    "first_published_at",
    "locale",
}


class TestV3SchemaDiscovery(TestV3Base, TestCase):
    def test_list_content_types(self):
        response = self.client.get(reverse("wagtailapi_v3:list_schemas"))
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertIn("types", content)
        names = [entry["name"] for entry in content["types"]]
        self.assertIn("pages", names)

    def test_get_pages_schema(self):
        response = self.client.get(
            reverse(
                "wagtailapi_v3:get_schema_for_type",
                kwargs={"type_name": "pages"},
            )
        )
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertIn("read", content)
        self.assertEqual(
            set(content["read"]["properties"].keys()), PAGE_READ_SCHEMA_FIELDS
        )
        meta_schema = content["read"]["$defs"]["PageMetaSchema"]
        self.assertEqual(
            set(meta_schema["properties"].keys()), PAGE_READ_META_SCHEMA_FIELDS
        )
        self.assertEqual(content["create"], {"description": "Not yet available."})
        self.assertEqual(content["patch"], {"description": "Not yet available."})

    def test_get_specific_page_type_schema_includes_create_schema(self):
        response = self.client.get(
            reverse(
                "wagtailapi_v3:get_schema_for_type",
                kwargs={"type_name": "tests.SimplePage"},
            )
        )
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertIn("title", content["create"]["properties"])
        self.assertIn("slug", content["create"]["properties"])

    def test_get_specific_page_type_schema_includes_patch_schema(self):
        response = self.client.get(
            reverse(
                "wagtailapi_v3:get_schema_for_type",
                kwargs={"type_name": "tests.SimplePage"},
            )
        )
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertIn("title", content["patch"]["properties"])
        self.assertIn("slug", content["patch"]["properties"])
        # Unlike create, the update/patch schema has no parent_id in its
        # meta - a page's parent can't be changed via this endpoint - and
        # title isn't required, since this is a partial update (only
        # `meta` itself, which every request needs to name the page type,
        # is required at the top level).
        meta_ref = content["patch"]["properties"]["meta"]["$ref"]
        meta_def_name = meta_ref.rsplit("/", 1)[-1]
        meta_schema = content["patch"]["$defs"][meta_def_name]
        self.assertNotIn("parent_id", meta_schema["properties"])
        self.assertEqual(content["patch"]["required"], ["meta"])

    def test_unknown_type_returns_404(self):
        response = self.client.get(
            reverse(
                "wagtailapi_v3:get_schema_for_type",
                kwargs={"type_name": "nope"},
            )
        )
        self.assertEqual(response.status_code, 404)
