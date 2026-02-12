from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.documents import get_document_model
from wagtail.models import Collection
from wagtail.test.utils import WagtailTestUtils

Document = get_document_model()


class TestBulkAddDocumentsToCollection(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.root_collection = Collection.get_first_root_node()
        self.dest_collection = self.root_collection.add_child(name="Destination")
        self.documents = [
            Document.objects.create(title=f"Test document - {i}") for i in range(1, 6)
        ]
        self.url = (
            reverse(
                "wagtail_bulk_action",
                args=(
                    "wagtaildocs",
                    "document",
                    "add_to_collection",
                ),
            )
            + "?"
        )
        for document in self.documents:
            self.url += f"id={document.id}&"
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
            "<p>You don't have permission to add these documents to a collection</p>",
            html,
        )

        for document in self.documents:
            self.assertInHTML(f"<li>{document.title}</li>", html)

        self.client.post(self.url, self.post_data)

        # Documents should not be moved to new collection
        for document in self.documents:
            self.assertEqual(
                Document.objects.get(id=document.id).collection_id,
                self.root_collection.id,
            )

    def test_simple(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtaildocs/bulk_actions/confirm_bulk_add_to_collection.html"
        )

    def test_add_to_collection(self):
        # Make post request
        response = self.client.post(self.url, self.post_data)

        # User should be redirected back to the index
        self.assertEqual(response.status_code, 302)

        # Documents should be moved to new collection
        for document in self.documents:
            self.assertEqual(
                Document.objects.get(id=document.id).collection_id,
                self.dest_collection.id,
            )


class TestBulkAddAllDocumentsToCollection(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.root_collection = Collection.get_first_root_node()
        self.dest_collection = self.root_collection.add_child(name="Destination")
        self.documents = [
            Document.objects.create(title=f"Test document - {i}") for i in range(1, 6)
        ]
        self.url = (
            reverse(
                "wagtail_bulk_action",
                args=(
                    "wagtaildocs",
                    "document",
                    "add_to_collection",
                ),
            )
            + "?id=all"
        )
        self.post_data = {"collection": str(self.dest_collection.id)}

    def test_add_all_to_collection_with_limited_permissions(self):
        # Create a group with document permissions on the source collection only
        self.other_collection = self.root_collection.add_child(name="Other")

        group = Group.objects.create(name="Other Collection Editors")
        self.other_collection.group_permissions.create(
            group=group, permission=Permission.objects.get(codename="change_document")
        )

        self.user.is_superuser = False
        self.user.groups.add(group)
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        # The user needs to have access to at least one document in order to access the bulk action page
        other_document = Document.objects.create(
            title="Test document - other", collection=self.other_collection
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        html = response.content.decode()

        self.assertInHTML(other_document.title, html)
        for document in self.documents:
            self.assertNotInHTML(f"<li>{document.title}</li>", html)

        self.client.post(self.url, self.post_data)

        # Documents should not be moved to new collection
        for document in self.documents:
            self.assertEqual(
                Document.objects.get(id=document.id).collection_id,
                self.root_collection.id,
            )

    def test_simple(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtaildocs/bulk_actions/confirm_bulk_add_to_collection.html"
        )

    def test_add_all_to_collection(self):
        # Make post request
        response = self.client.post(self.url, self.post_data)

        # User should be redirected back to the index
        self.assertEqual(response.status_code, 302)

        # Documents should be moved to new collection
        for document in self.documents:
            self.assertEqual(
                Document.objects.get(id=document.id).collection_id,
                self.dest_collection.id,
            )
