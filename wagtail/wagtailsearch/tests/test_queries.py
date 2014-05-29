from django.test import TestCase
from django.core import management
from wagtail.wagtailsearch import models
from wagtail.tests.utils import login, unittest
from StringIO import StringIO


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

    @unittest.expectedFailure # Time based popularity isn't implemented yet
    def test_query_popularity_over_time(self):
        today = timezone.now().date()
        two_days_ago = today - datetime.timedelta(days=2)
        a_week_ago = today - datetime.timedelta(days=7)
        a_month_ago = today - datetime.timedelta(days=30)

        # Add 10 hits to a query that was very popular query a month ago
        for i in range(10):
            models.Query.get("old popular query").add_hit(date=a_month_ago)

        # Add 5 hits to a query that is was popular 2 days ago
        for i in range(5):
            models.Query.get("new popular query").add_hit(date=two_days_ago)

        # Get most popular queries
        popular_queries = models.Query.get_most_popular()

        # Old popular query should be most popular
        self.assertEqual(popular_queries.count(), 2)
        self.assertEqual(popular_queries[0], models.Query.get("old popular query"))
        self.assertEqual(popular_queries[1], models.Query.get("new popular query"))

        # Get most popular queries for past week
        past_week_popular_queries = models.Query.get_most_popular(date_since=a_week_ago)

        # Only new popular query should be in this list
        self.assertEqual(past_week_popular_queries.count(), 1)
        self.assertEqual(past_week_popular_queries[0], models.Query.get("new popular query"))

        # Old popular query gets a couple more hits!
        for i in range(2):
            models.Query.get("old popular query").add_hit()

        # Old popular query should now be in the most popular queries
        self.assertEqual(past_week_popular_queries.count(), 2)
        self.assertEqual(past_week_popular_queries[0], models.Query.get("new popular query"))
        self.assertEqual(past_week_popular_queries[1], models.Query.get("old popular query"))


class TestGarbageCollectCommand(TestCase):
    def test_garbage_collect_command(self):
        management.call_command('search_garbage_collect', interactive=False, stdout=StringIO())

    # TODO: Test that this command is acctually doing its job


class TestQueryChooserView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get('/admin/search/queries/chooser/', params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)
