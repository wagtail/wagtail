from django.urls import reverse

from wagtail.models import CollectionViewRestriction

from .base import TestV3ImagesBase


class TestV3ImageListing(TestV3ImagesBase):
    def get_response(self, **params):
        return self.client.get(reverse("wagtailapi_v3:list_images"), params)

    def test_anonymous_can_list(self):
        response = self.get_response()
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertIn("count", content)
        self.assertIn("items", content)
        self.assertEqual(content["count"], 0)

    def test_listing_excludes_restricted_collection(self):
        restricted = self.create_collection("Secret")
        image = self.create_image(collection=restricted)
        CollectionViewRestriction.objects.create(
            collection=restricted,
            restriction_type=CollectionViewRestriction.LOGIN,
        )
        response = self.get_response()
        content = response.json()
        self.assertEqual(content["count"], 0)
        self.assertNotIn(image.id, [item["id"] for item in content["items"]])

    def test_listing_excludes_restricted_collection_descendant(self):
        parent = self.create_collection("Secret")
        child = self.create_collection("Child", parent=parent)
        image = self.create_image(collection=child)
        CollectionViewRestriction.objects.create(
            collection=parent,
            restriction_type=CollectionViewRestriction.LOGIN,
        )
        response = self.get_response()
        content = response.json()
        self.assertEqual(content["count"], 0)
        self.assertNotIn(image.id, [item["id"] for item in content["items"]])

    def test_meta_fields(self):
        self.create_image()
        response = self.get_response()
        item = response.json()["items"][0]
        self.assertEqual(
            set(item["meta"].keys()),
            {"type", "detail_url", "tags", "download_url"},
        )
        self.assertEqual(item["meta"]["type"], "wagtailimages.Image")

    def test_search_by_title(self):
        self.create_image(title="Wagtail bird")
        self.create_image(title="Bakery bun")
        response = self.get_response(search="Wagtail")
        content = response.json()
        self.assertEqual(content["count"], 1)
        self.assertEqual(content["items"][0]["title"], "Wagtail bird")

    def test_order_by_title(self):
        self.create_image(title="Alpha")
        self.create_image(title="Beta")
        response = self.get_response(order="title")
        titles = [item["title"] for item in response.json()["items"]]
        self.assertEqual(titles, ["Alpha", "Beta"])

    def test_filter_by_title(self):
        self.create_image(title="Alpha")
        self.create_image(title="Beta")
        response = self.get_response(title="Alpha")
        self.assertEqual(response.json()["count"], 1)

    def test_listing_prefetches_tags(self):
        for index in range(3):
            image = self.create_image(title=f"Image {index}")
            image.tags.add("one", "two")
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as captured:
            self.get_response()
        tag_queries = [
            query["sql"]
            for query in captured.captured_queries
            if "taggit_taggeditem" in query["sql"]
        ]
        # One prefetched tags query for the whole page, not one per image.
        self.assertEqual(len(tag_queries), 1)
