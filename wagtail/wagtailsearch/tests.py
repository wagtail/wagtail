from django.test import TestCase
from django.utils import timezone
import datetime
import unittest

import models
from wagtail.wagtailsearch.backends import get_search_backend


class TestSearch(TestCase):
    def test_search(self):
        # Get search backend and reset the index
        s = get_search_backend()
        s.reset_index()

        # Create a couple of objects and add them to the index
        testa = models.SearchTest()
        testa.title = "Hello World"
        testa.save()
        s.add(testa)

        testb = models.SearchTest()
        testb.title = "Hello"
        testb.save()
        s.add(testb)

        testc = models.SearchTestChild()
        testc.title = "Hello"
        testc.save()
        s.add(testc)

        # Refresh index
        s.refresh_index()

        # Ordinary search
        results = s.search("Hello", models.SearchTest)
        self.assertEqual(len(results), 3)

          # Ordinary search on "World"
        results = s.search("World", models.SearchTest)
        self.assertEqual(len(results), 1)

        # Searcher search
        results = models.SearchTest.title_search("Hello")
        self.assertEqual(len(results), 3)

        # Ordinary search on child
        results = s.search("Hello", models.SearchTestChild)
        self.assertEqual(len(results), 1)

        # Searcher search on child
        results = models.SearchTestChild.title_search("Hello")
        self.assertEqual(len(results), 1)

    def test_backend_loader(self):
        pass

    def test_hit_counter(self):
        # Add 10 hits to hello query
        for i in range(10):
            models.Query.get("Hello").add_hit()

        # Check that each hit was registered
        self.assertEqual(models.Query.get("Hello").hits, 10)

    def test_query_string_normalisation(self):
        # Get a query
        query = models.Query.get("Hello World!")

        # Check queries that should be the same
        self.assertEqual(query, models.Query.get("Hello World"))
        self.assertEqual(query, models.Query.get("Hello  World!!"))
        self.assertEqual(query, models.Query.get("hello world"))
        self.assertEqual(query, models.Query.get("Hello' world"))

        # Check queries that should be different
        self.assertNotEqual(query, models.Query.get("HelloWorld"))
        self.assertNotEqual(query, models.Query.get("Hello orld!!"))
        self.assertNotEqual(query, models.Query.get("Hello"))

    def test_popularity(self):
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
    def test_popularity_over_time(self):
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

    def test_editors_picks(self):
        pass

    def test_garbage_collect(self):
        pass