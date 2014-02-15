from django.test import TestCase
from django.conf import settings
from django.core import management
import unittest
from wagtail.wagtailsearch import models, get_search_backend
from wagtail.wagtailsearch.backends.elasticsearch import ElasticSearch
from StringIO import StringIO


# Register wagtailsearch signal handlers
from wagtail.wagtailsearch import register_signal_handlers
register_signal_handlers()


class BackendTests(object):
    def load_test_data(self):
        # Reset the index
        self.backend.reset_index()

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

    def test_prefetch_related(self):
        # Get results
        results = self.backend.search("Hello", models.SearchTest, prefetch_related=['content_type'])

        # Only testing that this doesn't crash!

    def test_object_indexed(self):
        # Attempt to index something that the models.SearchTest.object_indexed command says should be blocked
        test = models.SearchTest()
        test.title = "Don't index me!"
        test.save()
        self.backend.refresh_index()

        # Try to search for this record, It shouldn't be in the index
        results = self.backend.search("Don't index me!", models.SearchTest)
        self.assertEqual(len(results), 0)

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

    def test_results_len(self):
        # Get results
        results = self.backend.search("Hello", models.SearchTest)

        # Should return three results
        self.assertEqual(len(results), 3)

    def test_results2_len(self):
        # Get results for "World" terms
        results = self.backend.search("World", models.SearchTest)

        # Should return two results
        self.assertEqual(len(results), 2)

    def test_single_result_type(self):
        # Get a single result
        result = self.backend.search("Hello", models.SearchTest)[0]

        # Check that the result is a SearchTest object
        self.assertIsInstance(result, models.SearchTest)

    def test_sliced_results_len(self):
        # Get results and slice them
        sliced_results = self.backend.search("Hello", models.SearchTest)[1:3]

        # Slice must have a length of 2
        self.assertEqual(len(sliced_results), 2)

    def test_sliced_results_type(self):
        # Get results and slice them
        sliced_results = self.backend.search("Hello", models.SearchTest)[1:3]

        for result in sliced_results:
            # Check that the result is a SearchTest object
            self.assertIsInstance(result, models.SearchTest)

    def test_searcher_len(self):
        # Get results from searcher
        results = models.SearchTest.title_search("Hello")

        # Should return three results, just like before
        self.assertEqual(len(results), 3)

    def test_child_results_len(self):
        # Get results for child model
        results = self.backend.search("Hello", models.SearchTestChild)

        # Should return one object
        self.assertEqual(len(results), 1)

    def test_child_searcher_results_len(self):
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

    def test_reset_index(self):
        # Reset the index, this should clear out the index
        self.backend.reset_index()

        # Check that there are no results
        results = self.backend.search("Hello", models.SearchTest)
        self.assertEqual(len(results), 0)

    def test_update_index_command(self):
        # Reset the index, this should clear out the index
        self.backend.reset_index()

        # Run update_index command
        management.call_command('update_index', backend=self.backend, interactive=False, stdout=StringIO())

        # Check that there are still 3 results
        results = self.backend.search("Hello", models.SearchTest)
        self.assertEqual(len(results), 3)


class TestDBBackend(TestCase, BackendTests):
    def setUp(self):
        self.backend = get_search_backend('wagtail.wagtailsearch.backends.db.DBSearch')
        self.load_test_data()

    @unittest.expectedFailure
    def test_reset_index(self):
        super(TestDBBackend, self).test_reset_index()

    @unittest.expectedFailure
    def test_object_indexed(self):
        super(TestDBBackend, self).test_object_indexed()

    @unittest.expectedFailure
    def test_callable_indexed_field(self):
        super(TestDBBackend, self).test_callable_indexed_field()


class TestElasticSearchBackend(TestCase, BackendTests):
    def find_elasticsearch_backend(self):
        if hasattr(settings, 'WAGTAILSEARCH_BACKENDS'):
            for backend in settings.WAGTAILSEARCH_BACKENDS.keys():
                # Check that the backend is an elastic search backend
                if not isinstance(get_search_backend(backend), ElasticSearch):
                    continue

                # Check that tests are allowed on this backend
                if 'RUN_TESTS' not in settings.WAGTAILSEARCH_BACKENDS[backend]:
                    continue
                if settings.WAGTAILSEARCH_BACKENDS[backend]['RUN_TESTS'] is not True:
                    continue

                return backend

        # Backend not found
        raise unittest.SkipTest("Could not find an ElasticSearch backend")

    def setUp(self):
        self.backend = get_search_backend(self.find_elasticsearch_backend())
        self.load_test_data()


class TestBackendLoader(TestCase):
    pass
