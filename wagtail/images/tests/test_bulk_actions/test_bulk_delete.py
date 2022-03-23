from django.contrib.auth.models import Permission
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.test.utils import WagtailTestUtils

Image = get_image_model()
test_file = get_test_image_file()


class TestImageBulkDeleteView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()

        # Create images to delete
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
                    "delete",
                ),
            )
            + "?"
        )
        for image in self.images:
            self.url += f"id={image.id}&"

    def test_delete_with_limited_permissions(self):
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
            "<p>You don't have permission to delete these images</p>", html
        )

        for image in self.images:
            self.assertInHTML(
                "<li>{image_title}</li>".format(image_title=image.title), html
            )

        response = self.client.post(self.url)
        # User should be redirected back to the index
        self.assertEqual(response.status_code, 302)

        # Images should not be deleted
        for image in self.images:
            self.assertTrue(Image.objects.filter(id=image.id).exists())

    def test_simple(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailimages/bulk_actions/confirm_bulk_delete.html"
        )

    def test_delete(self):
        # Make post request
        response = self.client.post(self.url)

        # User should be redirected back to the index
        self.assertEqual(response.status_code, 302)

        # Images should be deleted
        for image in self.images:
            self.assertFalse(Image.objects.filter(id=image.id).exists())

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_usage_link(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailimages/bulk_actions/confirm_bulk_delete.html"
        )
        for image in self.images:
            self.assertContains(response, image.usage_url)
        # usage count should be printed for each image
        self.assertContains(response, "Used 0 times", count=5)
