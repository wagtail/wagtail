import json

from django.test import TestCase
from django.urls import reverse

PAGE_READ_SCHEMA_FIELDS = {"id", "title", "meta"}
PAGE_READ_META_SCHEMA_FIELDS = {
    "type",
    "detail_url",
    "html_url",
    "slug",
    "first_published_at",
}


class TestV3SchemaDiscovery(TestCase):
    def parse_json(self, response):
        return json.loads(response.content.decode("UTF-8"))

    def test_list_content_types(self):
        response = self.client.get(reverse("wagtailapi_v3:list_schemas"))
        self.assertEqual(response.status_code, 200)
        content = self.parse_json(response)
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
        content = self.parse_json(response)
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

    def test_unknown_type_returns_404(self):
        response = self.client.get(
            reverse(
                "wagtailapi_v3:get_schema_for_type",
                kwargs={"type_name": "nope"},
            )
        )
        self.assertEqual(response.status_code, 404)
