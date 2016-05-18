from __future__ import absolute_import, unicode_literals

import mock

from django.test import TestCase, override_settings

from wagtail.tests.search import models
from wagtail.tests.testapp.models import SimplePage
from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore.models import Page
from wagtail.wagtailsearch import index


class TestGetIndexedInstance(TestCase):
    def test_gets_instance(self):
        obj = models.SearchTest(
            title="Hello",
            live=True,
        )
        obj.save()

        # Should just return the object
        indexed_instance = index.get_indexed_instance(obj)
        self.assertEqual(indexed_instance, obj)

    def test_gets_specific_class(self):
        obj = models.SearchTestChild(
            title="Hello",
            live=True,
        )
        obj.save()

        # Running the command with the parent class should find the specific class again
        indexed_instance = index.get_indexed_instance(obj.searchtest_ptr)
        self.assertEqual(indexed_instance, obj)

    def test_blocks_not_in_indexed_objects(self):
        obj = models.SearchTestChild(
            title="Don't index me!",
            live=True,
        )
        obj.save()

        # We've told it not to index anything with the title "Don't index me"
        # get_indexed_instance should return None
        indexed_instance = index.get_indexed_instance(obj.searchtest_ptr)
        self.assertEqual(indexed_instance, None)


@mock.patch('wagtail.wagtailsearch.tests.DummySearchBackend', create=True)
@override_settings(WAGTAILSEARCH_BACKENDS={
    'default': {
        'BACKEND': 'wagtail.wagtailsearch.tests.DummySearchBackend'
    }
})
class TestInsertOrUpdateObject(TestCase, WagtailTestUtils):
    def test_inserts_object(self, backend):
        obj = models.SearchTest.objects.create(title="Test")
        index.insert_or_update_object(obj)

        backend().add.assert_called_with(obj)

    def test_doesnt_insert_unsaved_object(self, backend):
        obj = models.SearchTest(title="Test")
        index.insert_or_update_object(obj)

        self.assertFalse(backend().add.mock_calls)

    def test_converts_to_specific_page(self, backend):
        root_page = Page.objects.get(id=1)
        page = root_page.add_child(instance=SimplePage(title="test", slug="test", content="test"))

        # Convert page into a generic "Page" object and add it into the index
        unspecific_page = page.page_ptr
        index.insert_or_update_object(unspecific_page)

        # It should be automatically converted back to the specific version
        backend().add.assert_called_with(page)

    def test_catches_index_error(self, backend):
        obj = models.SearchTest.objects.create(title="Test")

        backend().add.side_effect = ValueError("Test")

        with self.assertLogs('wagtail.search.index', level='ERROR') as cm:
            index.insert_or_update_object(obj)

        self.assertEqual(len(cm.output), 1)
        self.assertIn("Exception raised while adding <SearchTest: Test> into the 'default' search backend", cm.output[0])
        self.assertIn("Traceback (most recent call last):", cm.output[0])
        self.assertIn("ValueError: Test", cm.output[0])


@mock.patch('wagtail.wagtailsearch.tests.DummySearchBackend', create=True)
@override_settings(WAGTAILSEARCH_BACKENDS={
    'default': {
        'BACKEND': 'wagtail.wagtailsearch.tests.DummySearchBackend'
    }
})
class TestRemoveObject(TestCase, WagtailTestUtils):
    def test_removes_object(self, backend):
        obj = models.SearchTest.objects.create(title="Test")
        index.remove_object(obj)

        backend().add.assert_called_with(obj)

    def test_removes_unsaved_object(self, backend):
        obj = models.SearchTest(title="Test")
        index.remove_object(obj)

        backend().delete.assert_called_with(obj)

    def test_catches_index_error(self, backend):
        obj = models.SearchTest.objects.create(title="Test")

        backend().delete.side_effect = ValueError("Test")

        with self.assertLogs('wagtail.search.index', level='ERROR') as cm:
            index.remove_object(obj)

        self.assertEqual(len(cm.output), 1)
        self.assertIn("Exception raised while deleting <SearchTest: Test> from the 'default' search backend", cm.output[0])
        self.assertIn("Traceback (most recent call last):", cm.output[0])
        self.assertIn("ValueError: Test", cm.output[0])
