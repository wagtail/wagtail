import swapper
from django.test import TestCase
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.test.utils import Page, WagtailTestUtils

PAGE_READ_SCHEMA_FIELDS = {"id", "title", "meta"}
PAGE_READ_META_SCHEMA_FIELDS = {
    "type",
    "warnings",
    "detail_url",
    "html_url",
    "slug",
    "first_published_at",
    "locale",
    "parent",
    "alias_of",
}
if not swapper.is_swapped("wagtailcore", "Page"):
    PAGE_READ_META_SCHEMA_FIELDS |= {"show_in_menus", "seo_title", "search_description"}


class TestV3SchemaDiscovery(TestV3Base, WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def test_anonymous_returns_401(self):
        self.unauthorize()
        response = self.client.get(reverse("wagtailapi_v3:list_schemas"))
        self.assert_problem_response(response, status_code=401)

    def test_list_content_types(self):
        response = self.client.get(reverse("wagtailapi_v3:list_schemas"))
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertIn("types", content)
        names = [entry["name"] for entry in content["types"]]
        self.assertIn(Page._meta.label, names)

    def test_get_pages_schema(self):
        response = self.client.get(
            reverse(
                "wagtailapi_v3:get_schema_for_type",
                kwargs={"type_name": Page._meta.label},
            )
        )
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertIn("read", content)
        self.assertEqual(
            set(content["read"]["properties"].keys()), PAGE_READ_SCHEMA_FIELDS
        )
        meta_schema = content["read"]["$defs"][f"{Page._meta.object_name}MetaSchema"]
        self.assertEqual(
            set(meta_schema["properties"].keys()), PAGE_READ_META_SCHEMA_FIELDS
        )
        self.assertEqual(content["create"], {"description": "Not available."})
        self.assertEqual(content["patch"], {"description": "Not available."})

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
        # title isn't required, since this is a partial update.
        # meta and meta.type are also optional, as they can be inferred from
        # the page ID.
        meta_any_of = content["patch"]["properties"]["meta"].get("anyOf")
        self.assertIsNotNone(meta_any_of)
        self.assertEqual(len(meta_any_of), 2)
        self.assertEqual(meta_any_of[1], {"type": "null"})
        meta_ref = meta_any_of[0]["$ref"]
        meta_def_name = meta_ref.rsplit("/", 1)[-1]
        meta_schema = content["patch"]["$defs"][meta_def_name]
        self.assertNotIn("parent_id", meta_schema["properties"])
        self.assertNotIn("meta", content["patch"].get("required", []))

    def test_unknown_type_returns_404(self):
        response = self.client.get(
            reverse(
                "wagtailapi_v3:get_schema_for_type",
                kwargs={"type_name": "nope"},
            )
        )
        self.assertEqual(response.status_code, 404)
