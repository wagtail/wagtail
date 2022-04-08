from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Collection
from wagtail.test.utils import WagtailTestUtils

Image = get_image_model()
test_file = get_test_image_file()


class TestBulkAddImagesToCollection(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()
        self.root_collection = Collection.get_first_root_node()
        self.dest_collection = self.root_collection.add_child(name="Destination")
        self.images = [
            Image.objects.create(title=f"Test image - {i}", file=test_file)
            for i in range(1, 6)
        ]
        self.url = (
            reverse(
                "wagtail_bulk_action",
                args=(
                    "wagtailimages",
                    "image",
                    "add_to_collection",
                ),
            )
            + "?"
        )
        for image in self.images:
            self.url += f"id={image.id}&"
        self.post_data = {"collection": str(self.dest_collection.id)}

    def test_add_to_collection_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        html = response.content.decode()
        self.assertInHTML(
            "<p>You don't have permission to add these images to a collection</p>", html
        )

        for image in self.images:
            self.assertInHTML(
                "<li>{image_title}</li>".format(image_title=image.title), html
            )

        response = self.client.post(self.url, self.post_data)

        # Images should not be moved to new collection
        for image in self.images:
            self.assertEqual(
                Image.objects.get(id=image.id).collection_id, self.root_collection.id
            )

    def test_simple(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailimages/bulk_actions/confirm_bulk_add_to_collection.html"
        )

    def test_add_to_collection(self):
        # Make post request
        response = self.client.post(self.url, self.post_data)

        # User should be redirected back to the index
        self.assertEqual(response.status_code, 302)

        # Images should be moved to new collection
        for image in self.images:
            self.assertEqual(
                Image.objects.get(id=image.id).collection_id, self.dest_collection.id
            )
