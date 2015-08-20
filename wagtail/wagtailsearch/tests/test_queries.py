import unittest
import warnings

from django.test import TestCase
from django.core import management
from django.utils.six import StringIO

from wagtail.utils.deprecation import RemovedInWagtail13Warning
from wagtail.wagtailsearch import models
from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailsearch.utils import normalise_query_string


class TestHitCounter(TestCase):
    def test_no_hits(self):
        self.assertEqual(models.Query.get("Hello").hits, 0)

    def test_hit(self):
        # Add a hit
        models.Query.get("Hello").add_hit()

        # Test
        self.assertEqual(models.Query.get("Hello").hits, 1)

    def test_10_hits(self):
        # Add 10 hits
        for i in range(10):
            models.Query.get("Hello").add_hit()

        # Test
        self.assertEqual(models.Query.get("Hello").hits, 10)


class TestQueryStringNormalisation(TestCase):
    def setUp(self):
        self.query = models.Query.get("Hello World!")

    def test_normalisation(self):
        self.assertEqual(str(self.query), "hello world")

    def test_equivilant_queries(self):
        queries = [
            "Hello World",
            "Hello  World!!",
            "hello world",
            "Hello' world",
        ]

        for query in queries:
            self.assertEqual(self.query, models.Query.get(query))

    def test_different_queries(self):
        queries = [
            "HelloWorld",
            "Hello orld!!",
            "Hello",
        ]

        for query in queries:
            self.assertNotEqual(self.query, models.Query.get(query))

    def test_truncation(self):
        test_querystring = 'a' * 1000
        result = normalise_query_string(test_querystring)
        self.assertEqual(len(result), 255)

    def test_no_truncation(self):
        test_querystring = 'a' * 10
        result = normalise_query_string(test_querystring)
        self.assertEqual(len(result), 10)


class TestQueryPopularity(TestCase):
    def test_query_popularity(self):
        # Add 3 hits to unpopular query
        for i in range(3):
            models.Query.get("unpopular query").add_hit()

        # Add 10 hits to popular query
        for i in range(10):
            models.Query.get("popular query").add_hit()

        # Get most popular queries
        popular_queries = models.Query.get_most_popular()

        # Check list
        self.assertEqual(popular_queries.count(), 2)
        self.assertEqual(popular_queries[0], models.Query.get("popular query"))
        self.assertEqual(popular_queries[1], models.Query.get("unpopular query"))

        # Add 5 hits to little popular query
        for i in range(5):
            models.Query.get("little popular query").add_hit()

        # Check list again, little popular query should be in the middle
        self.assertEqual(popular_queries.count(), 3)
        self.assertEqual(popular_queries[0], models.Query.get("popular query"))
        self.assertEqual(popular_queries[1], models.Query.get("little popular query"))
        self.assertEqual(popular_queries[2], models.Query.get("unpopular query"))

        # Unpopular query goes viral!
        for i in range(20):
            models.Query.get("unpopular query").add_hit()

        # Unpopular query should be most popular now
        self.assertEqual(popular_queries.count(), 3)
        self.assertEqual(popular_queries[0], models.Query.get("unpopular query"))
        self.assertEqual(popular_queries[1], models.Query.get("popular query"))
        self.assertEqual(popular_queries[2], models.Query.get("little popular query"))


class TestGarbageCollectCommand(TestCase):
    def test_garbage_collect_command(self):
        management.call_command('search_garbage_collect', interactive=False, stdout=StringIO())

    # TODO: Test that this command is acctually doing its job


class TestQueryChooserView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get('/admin/search/queries/chooser/', params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/queries/chooser/chooser.html')
        self.assertTemplateUsed(response, 'wagtailsearch/queries/chooser/chooser.js')

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)


class TestEditorsPickModelDeprecation(TestCase, WagtailTestUtils):
    """
    In Wagtail 1.1, the EditorsPick model was moved to a new
    "contrib.searchpromotions" module.

    The EditorsPick model was previously referenced in the search view in
    the project template in Wagtail 1.0.

    To help people upgrade, we've added a redirect to the new model which
    raises a DeprecationWarning. This TestCase tests that redirect.
    """
    def test_editors_pick_importable(self):
        from wagtail.wagtailsearch.models import EditorsPick
        # If the above line doesn't raise ImportError, this test passed

    def test_editors_pick_objects_attribute(self):
        """
        The Wagtail 1.0 project template used the .objects attribute so here,
        we test that still works as expected.
        """
        try:
            from wagtail.wagtailsearch.models import EditorsPick
        except ImportError:
            raise unittest.SkipTest("EditorsPick is not importable")

        self.reset_warning_registry()
        with warnings.catch_warnings(record=True) as w:
            queryset = EditorsPick.objects.all()

            # Check that a RemovedInWagtail13Warning has been triggered
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, RemovedInWagtail13Warning))
            self.assertTrue("The wagtailsearch.EditorsPick module has been moved to contrib.wagtailsearchpromotions.SearchPromotion" in str(w[-1].message))

        # Queryset must be of search promotions
        from wagtail.contrib.wagtailsearchpromotions.models import SearchPromotion
        self.assertTrue(issubclass(queryset.model, SearchPromotion))

    def test_editors_pick_init(self):
        """
        Just incase anyone manages to create an EditorsPick instance, make
        sure they get a warning
        """
        try:
            from wagtail.wagtailsearch.models import EditorsPick
        except ImportError:
            raise unittest.SkipTest("EditorsPick is not importable")

        self.reset_warning_registry()
        with warnings.catch_warnings(record=True) as w:
            ep = EditorsPick()

            # Check that a RemovedInWagtail13Warning has been triggered
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, RemovedInWagtail13Warning))
            self.assertTrue("The wagtailsearch.EditorsPick module has been moved to contrib.wagtailsearchpromotions.SearchPromotion" in str(w[-1].message))
