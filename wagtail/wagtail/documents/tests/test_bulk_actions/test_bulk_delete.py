from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode

from wagtail.documents import get_document_model
from wagtail.test.testapp.models import VariousOnDeleteModel
from wagtail.test.utils import WagtailTestUtils

Document = get_document_model()


class TestDocumentBulkDeleteView(WagtailTestUtils, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.documents = [
            Document.objects.create(title=f"Test document - {i}") for i in range(1, 6)
        ]
        cls.url = reverse(
            "wagtail_bulk_action",
            args=(Document._meta.app_label, Document._meta.model_name, "delete"),
        )
        cls.query_params = {
            "next": reverse("wagtaildocs:index"),
            "id": [item.pk for item in cls.documents],
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
            "<p>You don't have permission to delete these documents</p>", html
        )

        for document in self.documents:
            self.assertInHTML(f"<li>{document.title}</li>", html)

        response = self.client.post(self.url)
        # User should be redirected back to the index
        self.assertEqual(response.status_code, 302)

        # Documents should not be deleted
        for document in self.documents:
            self.assertTrue(Document.objects.filter(id=document.id).exists())

    def test_simple(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtaildocs/bulk_actions/confirm_bulk_delete.html"
        )

    def test_delete(self):
        # Make post request
        response = self.client.post(self.url)

        # User should be redirected back to the index
        self.assertEqual(response.status_code, 302)

        # Documents should be deleted
        for document in self.documents:
            self.assertFalse(Document.objects.filter(id=document.id).exists())

    def test_usage_link(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtaildocs/bulk_actions/confirm_bulk_delete.html"
        )
        for document in self.documents:
            self.assertContains(response, document.usage_url)
        # usage count should be printed for each document
        self.assertContains(response, "This document is referenced 0 times.", count=5)

    def test_delete_get_with_protected_reference(self):
        protected = self.documents[0]
        with self.captureOnCommitCallbacks(execute=True):
            VariousOnDeleteModel.objects.create(
                text="Undeletable",
                protected_document=protected,
            )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        main = soup.select_one("main")
        usage_link = main.find(
            "a",
            href=reverse("wagtaildocs:document_usage", args=[protected.pk])
            + "?describe_on_delete=1",
        )
        self.assertIsNotNone(usage_link)
        self.assertEqual(usage_link.text.strip(), "This document is referenced 1 time.")
        self.assertContains(
            response,
            "One or more references to this document prevent it from being deleted.",
        )
        submit_button = main.select_one("form button[type=submit]")
        self.assertIsNone(submit_button)
        back_button = main.find("a", href=reverse("wagtaildocs:index"))
        self.assertIsNotNone(back_button)
        self.assertEqual(back_button.text.strip(), "Go back")

    def test_delete_post_with_protected_reference(self):
        protected = self.documents[0]
        with self.captureOnCommitCallbacks(execute=True):
            VariousOnDeleteModel.objects.create(
                text="Undeletable",
                protected_document=protected,
            )
        response = self.client.post(self.url)

        # Should throw a PermissionDenied error and redirect to the dashboard
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("wagtailadmin_home"))
        self.assertEqual(
            response.context["message"],
            "Sorry, you do not have permission to access this area.",
        )

        # Check that the document is still here
        self.assertTrue(Document.objects.filter(pk=protected.pk).exists())
