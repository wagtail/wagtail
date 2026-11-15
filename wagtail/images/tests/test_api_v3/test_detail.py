from django.urls import reverse

from wagtail.models import CollectionViewRestriction

from .base import TestV3ImagesBase


class TestV3ImageDetail(TestV3ImagesBase):
    def get_response(self, image_id):
        return self.client.get(
            reverse("wagtailapi_v3:detail_image", kwargs={"image_id": image_id})
        )

    def test_anonymous_can_get_detail(self):
        image = self.create_image()
        response = self.get_response(image.id)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["id"], image.id)
        self.assertEqual(content["title"], "Test image")
        self.assertEqual(content["width"], 640)
        self.assertEqual(content["height"], 480)
        self.assertEqual(content["meta"]["type"], "wagtailimages.Image")
        self.assertIn("download_url", content["meta"])
        self.assertIsNotNone(content["meta"]["download_url"])

    def test_detail_excludes_restricted_collection(self):
        restricted = self.create_collection("Secret")
        image = self.create_image(collection=restricted)
        CollectionViewRestriction.objects.create(
            collection=restricted,
            restriction_type=CollectionViewRestriction.LOGIN,
        )
        response = self.get_response(image.id)
        self.assertEqual(response.status_code, 404)

    def test_detail_excludes_restricted_collection_descendant(self):
        parent = self.create_collection("Secret")
        child = self.create_collection("Child", parent=parent)
        image = self.create_image(collection=child)
        CollectionViewRestriction.objects.create(
            collection=parent,
            restriction_type=CollectionViewRestriction.LOGIN,
        )
        response = self.get_response(image.id)
        self.assertEqual(response.status_code, 404)

    def test_unknown_id_returns_404(self):
        response = self.get_response(999999)
        self.assertEqual(response.status_code, 404)
