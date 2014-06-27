from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings
from django.core import management
from wagtail.tests.utils import unittest
from wagtail.wagtailsearch import models, get_search_backend
from wagtail.wagtailsearch.backends.db import DBSearch
from wagtail.wagtailsearch.backends import InvalidSearchBackendError
from StringIO import StringIO


# Register wagtailsearch signal handlers
from wagtail.wagtailsearch import register_signal_handlers
register_signal_handlers()


class BackendTests(object):
    # To test a specific backend, subclass BackendTests and define self.backend_path.

    def setUp(self):
        # Search WAGTAILSEARCH_BACKENDS for an entry that uses the given backend path
        for (backend_name, backend_conf) in settings.WAGTAILSEARCH_BACKENDS.iteritems():
            if backend_conf['BACKEND'] == self.backend_path:
                self.backend = get_search_backend(backend_name)
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
        self.testa = testa

        testb = models.SearchTest()
        testb.title = "Hello"
        testb.live = True
        testb.save()

        testc = models.SearchTestChild()
        testc.title = "Hello"
        testc.live = True
        testc.save()

        testd = models.SearchTestChild()
        testd.title = "World"
        testd.save()

        # Refresh the index
        self.backend.refresh_index()

    def test_blank_search(self):
        # Get results for blank terms
        results = self.backend.search("", models.SearchTest)

        # Should return no results
        self.assertEqual(len(results), 0)

    def test_search(self):
        # Get results for "Hello"
        results = self.backend.search("Hello", models.SearchTest)

        # Should return three results
        self.assertEqual(len(results), 3)

        # Get results for "World"
        results = self.backend.search("World", models.SearchTest)

        # Should return two results
        self.assertEqual(len(results), 2)

    @unittest.skip("Need something to prefetch")
    def test_prefetch_related(self):
        # Get results
        results = self.backend.search("Hello", models.SearchTest, prefetch_related=['prefetch_field'])

        # Test both single result and multiple result (different code for each), only checking that this doesnt crash
        single_result = results[0]
        multi_result = results[:2]

    def test_callable_indexed_field(self):
        # Get results
        results = self.backend.search("Callable", models.SearchTest)

        # Should get all 4 results as they all have the callable indexed field
        self.assertEqual(len(results), 4)

    def test_filters(self):
        # Get only results with live=True set
        results = self.backend.search("Hello", models.SearchTest, filters=dict(live=True))

        # Should return two results
        self.assertEqual(len(results), 2)

    def test_single_result(self):
        # Get a single result
        result = self.backend.search("Hello", models.SearchTest)[0]

        # Check that the result is a SearchTest object
        self.assertIsInstance(result, models.SearchTest)

    def test_sliced_results(self):
        # Get results and slice them
        sliced_results = self.backend.search("Hello", models.SearchTest)[1:3]

        # Slice must have a length of 2
        self.assertEqual(len(sliced_results), 2)

        # Check that the results are SearchTest objects
        for result in sliced_results:
            self.assertIsInstance(result, models.SearchTest)

    def test_child_model(self):
        # Get results for child model
        results = self.backend.search("Hello", models.SearchTestChild)

        # Should return one object
        self.assertEqual(len(results), 1)

    def test_delete(self):
        # Delete one of the objects
        self.testa.delete()

        # Refresh index
        self.backend.refresh_index()

        # Check that there are only two results
        results = self.backend.search("Hello", models.SearchTest)
        self.assertEqual(len(results), 2)

    def test_update_index_command(self):
        # Reset the index, this should clear out the index
        self.backend.reset_index()

        # Run update_index command
        management.call_command('update_index', backend=self.backend, interactive=False, stdout=StringIO())

        # Check that there are still 3 results
        results = self.backend.search("Hello", models.SearchTest)
        self.assertEqual(len(results), 3)


class TestDBBackend(BackendTests, TestCase):
    backend_path = 'wagtail.wagtailsearch.backends.db.DBSearch'

    @unittest.expectedFailure
    def test_callable_indexed_field(self):
        super(TestDBBackend, self).test_callable_indexed_field()


class TestElasticSearchBackend(BackendTests, TestCase):
    backend_path = 'wagtail.wagtailsearch.backends.elasticsearch.ElasticSearch'

    def test_search_with_spaces_only(self):
        # Search for some space characters and hope it doesn't crash
        results = self.backend.search("   ", models.SearchTest)

        # Queries are lazily evaluated, force it to run
        list(results)

        # Didn't crash, yay!


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

    def test_nonexistant_backend_import(self):
        self.assertRaises(InvalidSearchBackendError, get_search_backend, backend='wagtail.wagtailsearch.backends.doesntexist.DoesntExist')

    def test_invalid_backend_import(self):
        self.assertRaises(InvalidSearchBackendError, get_search_backend, backend="I'm not a backend!")
