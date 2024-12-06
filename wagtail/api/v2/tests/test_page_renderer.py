import json

from django.test import TestCase
from django.test.utils import override_settings

from wagtail.test.utils import WagtailTestUtils


@override_settings(
    WAGTAIL_PAGE_RENDERERS=["wagtail.api.v2.renderers.APIV2PageRenderer"]
)
class TestPageRenderer(TestCase, WagtailTestUtils):
    fixtures = ["demosite.json"]

    def get_response(self, path, **params):
        return self.client.get(path, params, HTTP_ACCEPT="application/json; version=2")

    def test(self):
        response = self.get_response("/blog-index/blog-post/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-type"], "application/json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-type"], "application/json")

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode("UTF-8"))

        # Check the id field
        self.assertIn("id", content)
        self.assertEqual(content["id"], 16)

        # Check that the meta section is there
        self.assertIn("meta", content)
        self.assertIsInstance(content["meta"], dict)

        # Check the meta type
        self.assertIn("type", content["meta"])
        self.assertEqual(content["meta"]["type"], "demosite.BlogEntryPage")

        # Unline the standard API representation, this must not contain the detail_url
        self.assertNotIn("detail_url", content["meta"])

        # Check the meta html_url
        self.assertIn("html_url", content["meta"])
        self.assertEqual(
            content["meta"]["html_url"], "http://localhost/blog-index/blog-post/"
        )

        # Check the parent field
        self.assertIn("parent", content["meta"])
        self.assertIsInstance(content["meta"]["parent"], dict)
        self.assertEqual(set(content["meta"]["parent"].keys()), {"id", "meta", "title"})
        self.assertEqual(content["meta"]["parent"]["id"], 5)
        self.assertIsInstance(content["meta"]["parent"]["meta"], dict)
        self.assertEqual(
            set(content["meta"]["parent"]["meta"].keys()),
            {"type", "html_url"},
        )
        self.assertEqual(
            content["meta"]["parent"]["meta"]["type"], "demosite.BlogIndexPage"
        )
        self.assertEqual(
            content["meta"]["parent"]["meta"]["html_url"],
            "http://localhost/blog-index/",
        )

        # Check the alias_of field
        # See test_alias_page for a test on an alias page
        self.assertIn("alias_of", content["meta"])
        self.assertIsNone(content["meta"]["alias_of"])

        # Check that the custom fields are included
        self.assertIn("date", content)
        self.assertIn("body", content)
        self.assertIn("tags", content)
        self.assertIn("feed_image", content)
        self.assertIn("related_links", content)
        self.assertIn("carousel_items", content)

        # Check that the date was serialised properly
        self.assertEqual(content["date"], "2013-12-02")

        # Check that the tags were serialised properly
        self.assertEqual(content["tags"], ["bird", "wagtail"])

        # Check that the feed image was serialised properly
        self.assertIsInstance(content["feed_image"], dict)
        self.assertEqual(set(content["feed_image"].keys()), {"id", "meta"})
        self.assertEqual(content["feed_image"]["id"], 7)
        self.assertIsInstance(content["feed_image"]["meta"], dict)
        self.assertEqual(
            set(content["feed_image"]["meta"].keys()),
            {"type"},
        )
        self.assertEqual(content["feed_image"]["meta"]["type"], "wagtailimages.Image")

        # Check that the feed images' thumbnail was serialised properly
        self.assertEqual(
            content["feed_image_thumbnail"],
            {
                # This is OK because it tells us it used ImageRenditionField to generate the output
                "error": "SourceImageIOError"
            },
        )

        # Check that the child relations were serialised properly
        self.assertEqual(content["related_links"], [])
        for carousel_item in content["carousel_items"]:
            self.assertEqual(
                set(carousel_item.keys()),
                {"id", "meta", "embed_url", "link", "caption", "image"},
            )
            self.assertEqual(set(carousel_item["meta"].keys()), {"type"})
