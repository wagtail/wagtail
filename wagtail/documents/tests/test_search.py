import unittest

from django.core.files.base import ContentFile
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.six import b

from wagtail.documents import models
from wagtail.tests.utils import WagtailTestUtils


@override_settings(_WAGTAILSEARCH_FORCE_AUTO_UPDATE=['elasticsearch'])
class TestIssue613(TestCase, WagtailTestUtils):
    def get_elasticsearch_backend(self):
        from django.conf import settings
        from wagtail.search.backends import get_search_backend

        backend_path = 'wagtail.search.backends.elasticsearch'

        # Search WAGTAILSEARCH_BACKENDS for an entry that uses the given backend path
        for backend_name, backend_conf in settings.WAGTAILSEARCH_BACKENDS.items():
            if backend_conf['BACKEND'] == backend_path:
                return get_search_backend(backend_name)
        else:
            # no conf entry found - skip tests for this backend
            raise unittest.SkipTest("No WAGTAILSEARCH_BACKENDS entry for the backend %s" % backend_path)

    def setUp(self):
        self.search_backend = self.get_elasticsearch_backend()
        self.login()

    def add_document(self, **params):
        # Build a fake file
        fake_file = ContentFile(b("A boring example document"))
        fake_file.name = 'test.txt'

        # Submit
        post_data = {
            'title': "Test document",
            'file': fake_file,
        }
        post_data.update(params)
        response = self.client.post(reverse('wagtaildocs:add'), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtaildocs:index'))

        # Document should be created
        doc = models.Document.objects.filter(title=post_data['title'])
        self.assertTrue(doc.exists())
        return doc.first()

    def edit_document(self, **params):
        # Build a fake file
        fake_file = ContentFile(b("A boring example document"))
        fake_file.name = 'test.txt'

        # Create a document without tags to edit
        document = models.Document.objects.create(title="Test document", file=fake_file)

        # Build another fake file
        another_fake_file = ContentFile(b("A boring example document"))
        another_fake_file.name = 'test.txt'

        # Submit
        post_data = {
            'title': "Test document changed!",
            'file': another_fake_file,
        }
        post_data.update(params)
        response = self.client.post(reverse('wagtaildocs:edit', args=(document.id,)), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtaildocs:index'))

        # Document should be changed
        doc = models.Document.objects.filter(title=post_data['title'])
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
