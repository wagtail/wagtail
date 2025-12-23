from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode

from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.test.testapp.models import VariousOnDeleteModel
from wagtail.test.utils import WagtailTestUtils

Image = get_image_model()
test_file = get_test_image_file()


class TestImageBulkDeleteView(WagtailTestUtils, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.images = [
            Image.objects.create(title=f"Test image - {i}", file=test_file)
            for i in range(1, 6)
        ]
        cls.url = reverse(
            "wagtail_bulk_action",
            args=(Image._meta.app_label, Image._meta.model_name, "delete"),
        )
        cls.query_params = {
            "next": reverse("wagtailimages:index"),
            "id": [item.pk for item in cls.images],
        }
        cls.url += "?" + urlencode(cls.query_params, doseq=True)

    def setUp(self):
        self.user = self.login()

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
            self.assertInHTML(f"<li>{image.title}</li>", html)

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

    def test_usage_link(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailimages/bulk_actions/confirm_bulk_delete.html"
        )
        for image in self.images:
            self.assertContains(response, image.usage_url)
        # usage count should be printed for each image
        self.assertContains(response, "This image is referenced 0 times.", count=5)

    def test_delete_get_with_protected_reference(self):
        protected = self.images[0]
        with self.captureOnCommitCallbacks(execute=True):
            VariousOnDeleteModel.objects.create(
                text="Undeletable",
                protected_image=protected,
            )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        main = soup.select_one("main")
        usage_link = main.find(
            "a",
            href=reverse("wagtailimages:image_usage", args=[protected.pk])
            + "?describe_on_delete=1",
        )
        self.assertIsNotNone(usage_link)
        self.assertEqual(usage_link.text.strip(), "This image is referenced 1 time.")
        self.assertContains(
            response,
            "One or more references to this image prevent it from being deleted.",
        )
        submit_button = main.select_one("form button[type=submit]")
        self.assertIsNone(submit_button)
        back_button = main.find("a", href=reverse("wagtailimages:index"))
        self.assertIsNotNone(back_button)
        self.assertEqual(back_button.text.strip(), "Go back")

    def test_delete_post_with_protected_reference(self):
        protected = self.images[0]
        with self.captureOnCommitCallbacks(execute=True):
            VariousOnDeleteModel.objects.create(
                text="Undeletable",
                protected_image=protected,
            )
        response = self.client.post(self.url)

        # Should throw a PermissionDenied error and redirect to the dashboard
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("wagtailadmin_home"))
        self.assertEqual(
            response.context["message"],
            "Sorry, you do not have permission to access this area.",
        )

        # Check that the image is still here
        self.assertTrue(Image.objects.filter(pk=protected.pk).exists())
