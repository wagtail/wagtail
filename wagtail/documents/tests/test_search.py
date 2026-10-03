import unittest
from io import StringIO

from django.conf import settings
from django.core import management
from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse

from wagtail.documents import models
from wagtail.search.backends import get_search_backend
from wagtail.test.utils import WagtailTestUtils


class TestIssue613(WagtailTestUtils, TestCase):
    def setUp(self):
        if "elasticsearch" not in settings.WAGTAILSEARCH_BACKENDS:
            raise unittest.SkipTest("No elasticsearch backend active")

        self.login()

        management.call_command(
            "update_index",
            backend_name="elasticsearch",
            stdout=StringIO(),
            chunk_size=50,
        )

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
        # Note to future developer troubleshooting this test...
        # This test previously started by calling self.search_backend.reset_index(), but that was evidently redundant because
        # this was broken on Elasticsearch prior to the fix in
        # https://github.com/wagtail/wagtailsearch/commit/53a98169bccc3cef5b234944037f2b3f78efafd4 .
        # If this turns out to be necessary after all, you might want to compare how wagtail.tests.test_page_search.PageSearchTests does it.

        backend_conf = settings.WAGTAILSEARCH_BACKENDS["elasticsearch"].copy()
        backend_conf["AUTO_UPDATE"] = True
        with self.settings(
            WAGTAILSEARCH_BACKENDS={
                "elasticsearch": backend_conf,
            }
        ):
            search_backend = get_search_backend("elasticsearch")

            # Add a document with some tags
            document = self.add_document(tags="hello")

            search_backend.refresh_indexes()

            # Search for it by tag
            results = search_backend.search("hello", models.Document)

            # Check
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].id, document.id)

    def test_issue_613_on_edit(self):
        # Note to future developer troubleshooting this test...
        # This test previously started by calling self.search_backend.reset_index(), but that was evidently redundant because
        # this was broken on Elasticsearch prior to the fix in
        # https://github.com/wagtail/wagtailsearch/commit/53a98169bccc3cef5b234944037f2b3f78efafd4 .
        # If this turns out to be necessary after all, you might want to compare how wagtail.tests.test_page_search.PageSearchTests does it.

        backend_conf = settings.WAGTAILSEARCH_BACKENDS["elasticsearch"].copy()
        backend_conf["AUTO_UPDATE"] = True
        with self.settings(
            WAGTAILSEARCH_BACKENDS={
                "elasticsearch": backend_conf,
            }
        ):
            search_backend = get_search_backend("elasticsearch")

            # Add a document with some tags
            document = self.edit_document(tags="hello")

            search_backend.refresh_indexes()

            # Search for it by tag
            results = search_backend.search("hello", models.Document)

            # Check
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].id, document.id)
