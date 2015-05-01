from six import StringIO
import unittest
import time

from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings
from django.core import management

from wagtail.tests.utils import WagtailTestUtils
from wagtail.tests.search import models
from wagtail.wagtailsearch.backends import get_search_backend, InvalidSearchBackendError
from wagtail.wagtailsearch.backends.db import DBSearch


class BackendTests(WagtailTestUtils):
    # To test a specific backend, subclass BackendTests and define self.backend_path.

    def setUp(self):
        # Search WAGTAILSEARCH_BACKENDS for an entry that uses the given backend path
        for backend_name, backend_conf in settings.WAGTAILSEARCH_BACKENDS.items():
            if backend_conf['BACKEND'] == self.backend_path:
                self.backend = get_search_backend(backend_name)
                self.backend_name = backend_name
                break
        else:
            # no conf entry found - skip tests for this backend
            raise unittest.SkipTest("No WAGTAILSEARCH_BACKENDS entry for the backend %s" % self.backend_path)

        self.load_test_data()

    def load_test_data(self):
        # Reset the index
        self.backend.reset_index()
        self.backend.add_type(models.SearchTest)
        self.backend.add_type(models.SearchTestChild)

        # Create a test database
        testa = models.SearchTest()
        testa.title = "Hello World"
        testa.save()
        self.backend.add(testa)
        self.testa = testa

        testb = models.SearchTest()
        testb.title = "Hello"
        testb.live = True
        testb.save()
        self.backend.add(testb)
        self.testb = testb

        testc = models.SearchTestChild()
        testc.title = "Hello"
        testc.live = True
        testc.save()
        self.backend.add(testc)
        self.testc = testc

        testd = models.SearchTestChild()
        testd.title = "World"
        testd.save()
        self.backend.add(testd)
        self.testd = testd

        # Refresh the index
        self.backend.refresh_index()

    def test_blank_search(self):
        results = self.backend.search("", models.SearchTest)
        self.assertEqual(set(results), set())

    def test_search(self):
        results = self.backend.search("Hello", models.SearchTest)
        self.assertEqual(set(results), {self.testa, self.testb, self.testc.searchtest_ptr})

        results = self.backend.search("World", models.SearchTest)
        self.assertEqual(set(results), {self.testa, self.testd.searchtest_ptr})

    def test_callable_indexed_field(self):
        results = self.backend.search("Callable", models.SearchTest)
        self.assertEqual(set(results), {self.testa, self.testb, self.testc.searchtest_ptr, self.testd.searchtest_ptr})

    def test_filters(self):
        results = self.backend.search(None, models.SearchTest, filters=dict(live=True))
        self.assertEqual(set(results), {self.testb, self.testc.searchtest_ptr})

    def test_filters_with_in_lookup(self):
        live_page_titles = models.SearchTest.objects.filter(live=True).values_list('title', flat=True)
        results = self.backend.search(None, models.SearchTest, filters=dict(title__in=live_page_titles))
        self.assertEqual(set(results), {self.testb, self.testc.searchtest_ptr})

    def test_single_result(self):
        result = self.backend.search(None, models.SearchTest)[0]
        self.assertIsInstance(result, models.SearchTest)

    def test_sliced_results(self):
        sliced_results = self.backend.search(None, models.SearchTest)[1:3]

        self.assertEqual(len(sliced_results), 2)

        for result in sliced_results:
            self.assertIsInstance(result, models.SearchTest)

    def test_child_model(self):
        results = self.backend.search(None, models.SearchTestChild)
        self.assertEqual(set(results), {self.testc, self.testd})

    def test_delete(self):
        # Delete one of the objects
        self.backend.delete(self.testa)
        self.testa.delete()
        self.backend.refresh_index()

        results = self.backend.search(None, models.SearchTest)
        self.assertEqual(set(results), {self.testb, self.testc.searchtest_ptr, self.testd.searchtest_ptr})

    def test_update_index_command(self):
        # Reset the index, this should clear out the index
        self.backend.reset_index()

        # Give Elasticsearch some time to catch up...
        time.sleep(1)

        results = self.backend.search(None, models.SearchTest)
        self.assertEqual(set(results), set())

        # Run update_index command
        with self.ignore_deprecation_warnings():  # ignore any DeprecationWarnings thrown by models with old-style indexed_fields definitions
            management.call_command('update_index', backend_name=self.backend_name, interactive=False, stdout=StringIO())

        results = self.backend.search(None, models.SearchTest)
        self.assertEqual(set(results), {self.testa, self.testb, self.testc.searchtest_ptr, self.testd.searchtest_ptr})


@override_settings(WAGTAILSEARCH_BACKENDS={
    'default': {'BACKEND': 'wagtail.wagtailsearch.backends.db.DBSearch'}
})
class TestBackendLoader(TestCase):
    def test_import_by_name(self):
        db = get_search_backend(backend='default')
        self.assertIsInstance(db, DBSearch)

    def test_import_by_path(self):
        db = get_search_backend(backend='wagtail.wagtailsearch.backends.db.DBSearch')
        self.assertIsInstance(db, DBSearch)

    def test_nonexistent_backend_import(self):
        self.assertRaises(InvalidSearchBackendError, get_search_backend, backend='wagtail.wagtailsearch.backends.doesntexist.DoesntExist')

    def test_invalid_backend_import(self):
        self.assertRaises(InvalidSearchBackendError, get_search_backend, backend="I'm not a backend!")
