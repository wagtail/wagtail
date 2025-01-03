import unittest

from django.conf import settings
from django.core.files.base import ContentFile
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from wagtail.documents import models
from wagtail.search.backends import get_search_backend
from wagtail.test.utils import WagtailTestUtils


@override_settings(_WAGTAILSEARCH_FORCE_AUTO_UPDATE=["elasticsearch"])
class TestIssue613(WagtailTestUtils, TestCase):
    def get_elasticsearch_backend(self):
        if "elasticsearch" not in settings.WAGTAILSEARCH_BACKENDS:
            raise unittest.SkipTest("No elasticsearch backend active")

        return get_search_backend("elasticsearch")

    def setUp(self):
        self.search_backend = self.get_elasticsearch_backend()
        self.login()

    def add_document(self, **params):
        # Build a fake file
        fake_file = ContentFile(b"A boring example document")
        fake_file.name = "test.txt"

        # Submit
        post_data = {
            "title": "Test document",
            "file": fake_file,
        }
        post_data.update(params)
        response = self.client.post(reverse("wagtaildocs:add"), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse("wagtaildocs:index"))

        # Document should be created
        doc = models.Document.objects.filter(title=post_data["title"])
        self.assertTrue(doc.exists())
        return doc.first()

    def edit_document(self, **params):
        # Build a fake file
        fake_file = ContentFile(b"A boring example document")
        fake_file.name = "test.txt"

        # Create a document without tags to edit
        document = models.Document.objects.create(title="Test document", file=fake_file)

        # Build another fake file
        another_fake_file = ContentFile(b"A boring example document")
        another_fake_file.name = "test.txt"

        # Submit
        post_data = {
            "title": "Test document changed!",
            "file": another_fake_file,
        }
        post_data.update(params)
        response = self.client.post(
            reverse("wagtaildocs:edit", args=(document.id,)), post_data
        )

        # User should be redirected back to the index
        self.assertRedirects(response, reverse("wagtaildocs:index"))

        # Document should be changed
        doc = models.Document.objects.filter(title=post_data["title"])
        self.assertTrue(doc.exists())
        return doc.first()

    def test_issue_613_on_add(self):
        # Reset the search index
        self.search_backend.reset_index()
        self.search_backend.add_type(models.Document)

        # Add a document with some tags
        document = self.add_document(tags="hello")
        self.search_backend.refresh_index()

        # Search for it by tag
        results = self.search_backend.search("hello", models.Document)

        # Check
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, document.id)

    def test_issue_613_on_edit(self):
        # Reset the search index
        self.search_backend.reset_index()
        self.search_backend.add_type(models.Document)

        # Add a document with some tags
        document = self.edit_document(tags="hello")
        self.search_backend.refresh_index()

        # Search for it by tag
        results = self.search_backend.search("hello", models.Document)

        # Check
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, document.id)


class TestIssue12627(WagtailTestUtils, TestCase):
    def get_elasticsearch_backend(self):
        if "elasticsearch" not in settings.WAGTAILSEARCH_BACKENDS:
            raise unittest.SkipTest("No elasticsearch backend active")

        return get_search_backend("elasticsearch")

    def setUp(self):
        self.search_backend = self.get_elasticsearch_backend()
        self.login()

    def add_document(self, created_at=None):
        # Build a fake file
        fake_file = ContentFile(b"An example document")
        fake_file.name = "test.txt"

        # Create document
        document = models.Document.objects.create(
            title="Test Document",
            file=fake_file,
            created_at=created_at,
        )

        return document

    def test_filter_by_created_at(self):
        # Reset the search index
        self.search_backend.reset_index()
        self.search_backend.add_type(models.Document)

        # Add two documents with different creation dates
        doc1 = self.add_document(created_at="2025-01-04")
        doc2 = self.add_document(created_at="2025-01-02")
        doc3 = self.add_document(created_at="2025-01-03")
        doc4 = self.add_document(created_at="2025-01-01")

        # Index the documents
        self.search_backend.add(doc1)
        self.search_backend.add(doc2)
        self.search_backend.add(doc3)
        self.search_backend.add(doc4)
        self.search_backend.refresh_index()

        # Search and filter by created_at
        results = self.search_backend.search(
            None,
            models.Document,
            filters={"created_at__date": "2025-01-01"},
        )

        # Check
        self.assertEqual(len(results), 4)
        self.assertTrue(results[0].id, doc4.id)
        self.assertTrue(results[1].id, doc2.id)
        self.assertTrue(results[2].id, doc3.id)
        self.assertTrue(results[3].id, doc1.id)
