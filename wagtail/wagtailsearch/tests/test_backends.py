import unittest
import time

from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings
from django.core import management
from django.utils.six import StringIO

from wagtail.tests.utils import WagtailTestUtils
from wagtail.tests.search import models
from wagtail.wagtailsearch.backends import get_search_backend, get_search_backends, InvalidSearchBackendError
from wagtail.wagtailsearch.backends.db import DBSearchIndex


class BackendTests(WagtailTestUtils):
    # To test a specific backend, subclass BackendTests and define self.backend_path.

    def setUp(self):
        # Search WAGTAILSEARCH_BACKENDS for an entry that uses the given backend path
        for index_name, index_conf in settings.WAGTAILSEARCH_BACKENDS.items():
            if index_conf['BACKEND'] == self.backend_path:
                self.index = get_search_backend(index_name)
                self.index_name = index_name
                break
        else:
            # no index conf entry found - skip tests for this backend
            raise unittest.SkipTest("No WAGTAILSEARCH_BACKENDS entry for the backend %s" % self.backend_path)

        self.load_test_data()

    def load_test_data(self):
        # Reset the index
        self.index.reset_index()
        self.index.add_type(models.SearchTest)
        self.index.add_type(models.SearchTestChild)

        # Create a test database
        testa = models.SearchTest()
        testa.title = "Hello World"
        testa.save()
        self.index.add(testa)
        self.testa = testa

        testb = models.SearchTest()
        testb.title = "Hello"
        testb.live = True
        testb.save()
        self.index.add(testb)
        self.testb = testb

        testc = models.SearchTestChild()
        testc.title = "Hello"
        testc.live = True
        testc.save()
        self.index.add(testc)
        self.testc = testc

        testd = models.SearchTestChild()
        testd.title = "World"
        testd.save()
        self.index.add(testd)
        self.testd = testd

        # Refresh the index
        self.index.refresh_index()

    def test_blank_search(self):
        results = self.index.search("", models.SearchTest)
        self.assertEqual(set(results), set())

    def test_search(self):
        results = self.index.search("Hello", models.SearchTest)
        self.assertEqual(set(results), {self.testa, self.testb, self.testc.searchtest_ptr})

        results = self.index.search("World", models.SearchTest)
        self.assertEqual(set(results), {self.testa, self.testd.searchtest_ptr})

    def test_operator_or(self):
        # All records that match any term should be returned
        results = self.index.search("Hello world", models.SearchTest, operator='or')

        self.assertEqual(set(results), {self.testa, self.testb, self.testc.searchtest_ptr, self.testd.searchtest_ptr})

    def test_operator_and(self):
        # Records must match all search terms to be returned
        results = self.index.search("Hello world", models.SearchTest, operator='and')

        self.assertEqual(set(results), {self.testa})

    def test_callable_indexed_field(self):
        results = self.index.search("Callable", models.SearchTest)
        self.assertEqual(set(results), {self.testa, self.testb, self.testc.searchtest_ptr, self.testd.searchtest_ptr})

    def test_filters(self):
        results = self.index.search(None, models.SearchTest, filters=dict(live=True))
        self.assertEqual(set(results), {self.testb, self.testc.searchtest_ptr})

    def test_filters_with_in_lookup(self):
        live_page_titles = models.SearchTest.objects.filter(live=True).values_list('title', flat=True)
        results = self.index.search(None, models.SearchTest, filters=dict(title__in=live_page_titles))
        self.assertEqual(set(results), {self.testb, self.testc.searchtest_ptr})

    def test_single_result(self):
        result = self.index.search(None, models.SearchTest)[0]
        self.assertIsInstance(result, models.SearchTest)

    def test_sliced_results(self):
        sliced_results = self.index.search(None, models.SearchTest)[1:3]

        self.assertEqual(len(sliced_results), 2)

        for result in sliced_results:
            self.assertIsInstance(result, models.SearchTest)

    def test_child_model(self):
        results = self.index.search(None, models.SearchTestChild)
        self.assertEqual(set(results), {self.testc, self.testd})

    def test_child_model_with_id_filter(self):
        results = self.index.search("World", models.SearchTestChild.objects.filter(id=self.testd.id))
        self.assertEqual(set(results), {self.testd})

    def test_delete(self):
        # Delete one of the objects
        self.index.delete(self.testa)
        self.testa.delete()
        self.index.refresh_index()

        results = self.index.search(None, models.SearchTest)
        self.assertEqual(set(results), {self.testb, self.testc.searchtest_ptr, self.testd.searchtest_ptr})

    def test_update_index_command(self):
        # Reset the index, this should clear out the index
        self.index.reset_index()

        # Give Elasticsearch some time to catch up...
        time.sleep(1)

        results = self.index.search(None, models.SearchTest)
        self.assertEqual(set(results), set())

        # Run update_index command
        with self.ignore_deprecation_warnings():
            # ignore any DeprecationWarnings thrown by models with old-style indexed_fields definitions
            management.call_command(
                'update_index', index_name=self.index_name, interactive=False, stdout=StringIO()
            )

        results = self.index.search(None, models.SearchTest)
        self.assertEqual(set(results), {self.testa, self.testb, self.testc.searchtest_ptr, self.testd.searchtest_ptr})


@override_settings(
    WAGTAILSEARCH_BACKENDS={
        'default': {'BACKEND': 'wagtail.wagtailsearch.backends.db'}
    }
)
class TestBackendLoader(TestCase):
    def test_import_by_name(self):
        index = get_search_backend(backend='default')
        self.assertIsInstance(index, DBSearchIndex)

    def test_import_by_path(self):
        index = get_search_backend(backend='wagtail.wagtailsearch.backends.db')
        self.assertIsInstance(index, DBSearchIndex)

    def test_import_by_full_path(self):
        index = get_search_backend(backend='wagtail.wagtailsearch.backends.db.DBSearchIndex')
        self.assertIsInstance(index, DBSearchIndex)

    def test_nonexistent_backend_import(self):
        self.assertRaises(
            InvalidSearchBackendError, get_search_backend, backend='wagtail.wagtailsearch.backends.doesntexist'
        )

    def test_invalid_backend_import(self):
        self.assertRaises(InvalidSearchBackendError, get_search_backend, backend="I'm not a backend!")

    def test_get_search_backends(self):
        indices = list(get_search_backends())

        self.assertEqual(len(indices), 1)
        self.assertIsInstance(indices[0], DBSearchIndex)

    @override_settings(
        WAGTAILSEARCH_BACKENDS={
            'default': {
                'BACKEND': 'wagtail.wagtailsearch.backends.db'
            },
            'another-index': {
                'BACKEND': 'wagtail.wagtailsearch.backends.db'
            },
        }
    )
    def test_get_search_backends_multiple(self):
        indices = list(get_search_backends())

        self.assertEqual(len(indices), 2)

    def test_get_search_backends_with_auto_update(self):
        indices = list(get_search_backends(with_auto_update=True))

        # Auto update is the default
        self.assertEqual(len(indices), 1)

    @override_settings(
        WAGTAILSEARCH_BACKENDS={
            'default': {
                'BACKEND': 'wagtail.wagtailsearch.backends.db',
                'AUTO_UPDATE': False,
            },
        }
    )
    def test_get_search_backends_with_auto_update_disabled(self):
        indices = list(get_search_backends(with_auto_update=True))

        self.assertEqual(len(indices), 0)

    @override_settings(
        WAGTAILSEARCH_BACKENDS={
            'default': {
                'BACKEND': 'wagtail.wagtailsearch.backends.db',
                'AUTO_UPDATE': False,
            },
        }
    )
    def test_get_search_backends_without_auto_update_disabled(self):
        indices = list(get_search_backends())

        self.assertEqual(len(indices), 1)
