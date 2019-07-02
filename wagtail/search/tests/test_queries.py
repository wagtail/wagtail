import datetime
import json
from io import StringIO

from django.core import management
from django.test import SimpleTestCase, TestCase

from wagtail.contrib.search_promotions.models import SearchPromotion
from wagtail.search import models
from wagtail.search.utils import normalise_query_string, separate_filters_from_query
from wagtail.tests.utils import WagtailTestUtils


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
        self.query = models.Query.get("  Hello  World!  ")

    def test_normalisation(self):
        self.assertEqual(str(self.query), "hello world!")

    def test_equivalent_queries(self):
        queries = [
            "  Hello World!",
            "Hello World!  ",
            "hello  world!",
            "  Hello  world!  ",
        ]

        for query in queries:
            self.assertEqual(self.query, models.Query.get(query))

    def test_different_queries(self):
        queries = [
            "HelloWorld",
            "HelloWorld!"
            "  Hello  World!  ",
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
        nowdt = datetime.datetime.now()
        old_hit_date = (nowdt - datetime.timedelta(days=14)).date()
        recent_hit_date = (nowdt - datetime.timedelta(days=1)).date()

        # Add 10 hits that are more than one week old ; the related queries and the daily hits
        # should be deleted bu the search_garbage_collect command.
        querie_ids_to_be_deleted = []
        for i in range(10):
            q = models.Query.get("Hello {}".format(i))
            q.add_hit(date=old_hit_date)
            querie_ids_to_be_deleted.append(q.id)

        # Add 10 hits that are less than one week old ; these ones should not be deleted.
        recent_querie_ids = []
        for i in range(10):
            q = models.Query.get("World {}".format(i))
            q.add_hit(date=recent_hit_date)
            recent_querie_ids.append(q.id)

        # Add 10 queries that are promoted. These ones should not be deleted.
        promoted_querie_ids = []
        for i in range(10):
            q = models.Query.get("Foo bar {}".format(i))
            q.add_hit(date=old_hit_date)
            SearchPromotion.objects.create(query=q, page_id=1, sort_order=0, description='Test')
            promoted_querie_ids.append(q.id)

        management.call_command('search_garbage_collect', stdout=StringIO())

        self.assertFalse(models.Query.objects.filter(id__in=querie_ids_to_be_deleted).exists())
        self.assertFalse(models.QueryDailyHits.objects.filter(
            date=old_hit_date, query_id__in=querie_ids_to_be_deleted).exists())

        self.assertEqual(models.Query.objects.filter(id__in=recent_querie_ids).count(), 10)
        self.assertEqual(models.QueryDailyHits.objects.filter(
            date=recent_hit_date, query_id__in=recent_querie_ids).count(), 10)

        self.assertEqual(models.Query.objects.filter(id__in=promoted_querie_ids).count(), 10)
        self.assertEqual(models.QueryDailyHits.objects.filter(
            date=recent_hit_date, query_id__in=promoted_querie_ids).count(), 0)


class TestQueryChooserView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get('/admin/search/queries/chooser/', params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/queries/chooser/chooser.html')
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['step'], 'chooser')

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)


class TestSeparateFiltersFromQuery(SimpleTestCase):
    def test_only_query(self):
        filters, query = separate_filters_from_query('hello world')

        self.assertDictEqual(filters, {})
        self.assertEqual(query, 'hello world')

    def test_filter(self):
        filters, query = separate_filters_from_query('author:foo')

        self.assertDictEqual(filters, {'author': 'foo'})
        self.assertEqual(query, '')

    def test_filter_with_quotation_mark(self):
        filters, query = separate_filters_from_query('author:"foo bar"')

        self.assertDictEqual(filters, {'author': 'foo bar'})
        self.assertEqual(query, '')

    def test_filter_and_query(self):
        filters, query = separate_filters_from_query('author:foo hello world')

        self.assertDictEqual(filters, {'author': 'foo'})
        self.assertEqual(query, 'hello world')

    def test_filter_with_quotation_mark_and_query(self):
        filters, query = separate_filters_from_query('author:"foo bar" hello world')

        self.assertDictEqual(filters, {'author': 'foo bar'})
        self.assertEqual(query, 'hello world')

    def test_filter_with_unclosed_quotation_mark_and_query(self):
        filters, query = separate_filters_from_query('author:"foo bar hello world')

        self.assertDictEqual(filters, {})
        self.assertEqual(query, 'author:"foo bar hello world')

    def test_two_filters_and_query(self):
        filters, query = separate_filters_from_query('author:"foo bar" hello world bar:beer')

        self.assertDictEqual(filters, {'author': 'foo bar', 'bar': 'beer'})
        self.assertEqual(query, 'hello world')
