from datetime import date
from unittest import mock

from django.test import TestCase, override_settings

from wagtail.core.models import Page
from wagtail.search import index
from wagtail.tests.search import models
from wagtail.tests.testapp.models import SimplePage
from wagtail.tests.utils import WagtailTestUtils


class TestGetIndexedInstance(TestCase):
    fixtures = ['search']

    def test_gets_instance(self):
        obj = models.Author.objects.get(id=1)

        # Should just return the object
        indexed_instance = index.get_indexed_instance(obj)
        self.assertEqual(indexed_instance, obj)

    def test_gets_specific_class(self):
        obj = models.Novel.objects.get(id=1)

        # Running the command with the parent class should find the specific class again
        indexed_instance = index.get_indexed_instance(obj.book_ptr)
        self.assertEqual(indexed_instance, obj)

    def test_blocks_not_in_indexed_objects(self):
        obj = models.Novel(
            title="Don't index me!",
            publication_date=date(2017, 10, 18),
            number_of_pages=100
        )
        obj.save()

        # We've told it not to index anything with the title "Don't index me"
        # get_indexed_instance should return None
        indexed_instance = index.get_indexed_instance(obj.book_ptr)
        self.assertEqual(indexed_instance, None)


@mock.patch('wagtail.search.tests.DummySearchBackend', create=True)
@override_settings(WAGTAILSEARCH_BACKENDS={
    'default': {
        'BACKEND': 'wagtail.search.tests.DummySearchBackend'
    }
})
class TestInsertOrUpdateObject(TestCase, WagtailTestUtils):
    def test_inserts_object(self, backend):
        obj = models.Book.objects.create(title="Test", publication_date=date(2017, 10, 18), number_of_pages=100)
        backend().reset_mock()

        index.insert_or_update_object(obj)

        backend().add.assert_called_with(obj)

    def test_doesnt_insert_unsaved_object(self, backend):
        obj = models.Book(title="Test", publication_date=date(2017, 10, 18), number_of_pages=100)
        backend().reset_mock()

        index.insert_or_update_object(obj)

        self.assertFalse(backend().add.mock_calls)

    def test_converts_to_specific_page(self, backend):
        root_page = Page.objects.get(id=1)
        page = root_page.add_child(instance=SimplePage(title="test", slug="test", content="test"))

        # Convert page into a generic "Page" object and add it into the index
        unspecific_page = page.page_ptr

        backend().reset_mock()

        index.insert_or_update_object(unspecific_page)

        # It should be automatically converted back to the specific version
        backend().add.assert_called_with(page)

    def test_catches_index_error(self, backend):
        obj = models.Book.objects.create(title="Test", publication_date=date(2017, 10, 18), number_of_pages=100)

        backend().add.side_effect = ValueError("Test")
        backend().reset_mock()

        with self.assertLogs('wagtail.search.index', level='ERROR') as cm:
            index.insert_or_update_object(obj)

        self.assertEqual(len(cm.output), 1)
        self.assertIn("Exception raised while adding <Book: Test> into the 'default' search backend", cm.output[0])
        self.assertIn("Traceback (most recent call last):", cm.output[0])
        self.assertIn("ValueError: Test", cm.output[0])


@mock.patch('wagtail.search.tests.DummySearchBackend', create=True)
@override_settings(WAGTAILSEARCH_BACKENDS={
    'default': {
        'BACKEND': 'wagtail.search.tests.DummySearchBackend'
    }
})
class TestRemoveObject(TestCase, WagtailTestUtils):
    def test_removes_object(self, backend):
        obj = models.Book.objects.create(title="Test", publication_date=date(2017, 10, 18), number_of_pages=100)
        backend().reset_mock()

        index.remove_object(obj)

        backend().delete.assert_called_with(obj)

    def test_removes_unsaved_object(self, backend):
        obj = models.Book(title="Test", publication_date=date(2017, 10, 18), number_of_pages=100)
        backend().reset_mock()

        index.remove_object(obj)

        backend().delete.assert_called_with(obj)

    def test_catches_index_error(self, backend):
        obj = models.Book.objects.create(title="Test", publication_date=date(2017, 10, 18), number_of_pages=100)
        backend().reset_mock()

        backend().delete.side_effect = ValueError("Test")

        with self.assertLogs('wagtail.search.index', level='ERROR') as cm:
            index.remove_object(obj)

        self.assertEqual(len(cm.output), 1)
        self.assertIn("Exception raised while deleting <Book: Test> from the 'default' search backend", cm.output[0])
        self.assertIn("Traceback (most recent call last):", cm.output[0])
        self.assertIn("ValueError: Test", cm.output[0])


@mock.patch('wagtail.search.tests.DummySearchBackend', create=True)
@override_settings(WAGTAILSEARCH_BACKENDS={
    'default': {
        'BACKEND': 'wagtail.search.tests.DummySearchBackend'
    }
})
class TestSignalHandlers(TestCase, WagtailTestUtils):
    def test_index_on_create(self, backend):
        backend().reset_mock()
        obj = models.Book.objects.create(title="Test", publication_date=date(2017, 10, 18), number_of_pages=100)
        backend().add.assert_called_with(obj)

    def test_index_on_update(self, backend):
        obj = models.Book.objects.create(title="Test", publication_date=date(2017, 10, 18), number_of_pages=100)

        backend().reset_mock()
        obj.title = "Updated test"
        obj.save()

        self.assertEqual(backend().add.call_count, 1)
        indexed_object = backend().add.call_args[0][0]
        self.assertEqual(indexed_object.title, "Updated test")

    def test_index_on_delete(self, backend):
        obj = models.Book.objects.create(title="Test", publication_date=date(2017, 10, 18), number_of_pages=100)

        backend().reset_mock()
        obj.delete()
        backend().delete.assert_called_with(obj)

    def test_do_not_index_fields_omitted_from_update_fields(self, backend):
        obj = models.Book.objects.create(title="Test", publication_date=date(2017, 10, 18), number_of_pages=100)

        backend().reset_mock()
        obj.title = "Updated test"
        obj.publication_date = date(2001, 10, 19)
        obj.save(update_fields=['title'])

        self.assertEqual(backend().add.call_count, 1)
        indexed_object = backend().add.call_args[0][0]
        self.assertEqual(indexed_object.title, "Updated test")
        self.assertEqual(indexed_object.publication_date, date(2017, 10, 18))
