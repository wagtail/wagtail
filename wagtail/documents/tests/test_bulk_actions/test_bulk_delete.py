from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.documents import get_document_model
from wagtail.test.utils import WagtailTestUtils

Document = get_document_model()


class TestDocumentBulkDeleteView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()

        # Create documents to delete
        self.documents = [
            Document.objects.create(title=f"Test document - {i}") for i in range(1, 6)
        ]
        self.url = (
            reverse(
                "wagtail_bulk_action",
                args=(
                    "wagtaildocs",
                    "document",
                    "delete",
                ),
            )
            + "?"
        )
        for document in self.documents:
            self.url += f"id={document.id}&"

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
            self.assertInHTML(
                "<li>{document_title}</li>".format(document_title=document.title), html
            )

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
        self.assertContains(response, "Used 0 times", count=5)
