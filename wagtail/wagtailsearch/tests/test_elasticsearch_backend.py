import unittest2 as unittest
import json
import datetime

from django.test import TestCase
from django.db.models import Q

from wagtail.wagtailsearch.backends.elasticsearch import ElasticSearchQuery
from wagtail.tests import models
from .test_backends import BackendTests


class TestElasticSearchBackend(BackendTests, TestCase):
    backend_path = 'wagtail.wagtailsearch.backends.elasticsearch.ElasticSearch'


class TestElasticSearchQuery(TestCase):
    def assertDictEqual(self, a, b):
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_simple(self):
        # Create a query
        query = ElasticSearchQuery(models.SearchTest.objects.all(), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}]},'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_filter(self):
        # Create a query
        query = ElasticSearchQuery(models.SearchTest.objects.filter(title="Test"), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'and': [{'term': {'title': 'Test'}}]}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_and_filter(self):
        # Create a query
        query = ElasticSearchQuery(models.SearchTest.objects.filter(title="Test", live=True), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'and': [{'term': {'live': True}}, {'term': {'title': 'Test'}}]}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_or_filter(self):
        # Create a query
        query = ElasticSearchQuery(models.SearchTest.objects.filter(Q(title="Test") | Q(live=True)), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'and': [{'or': [{'term': {'title': 'Test'}}, {'term': {'live': True}}]}]}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_negated_filter(self):
        # Create a query
        query = ElasticSearchQuery(models.SearchTest.objects.exclude(live=True), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'and': [{'not': {'and': [{'term': {'live': True}}]}}]}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_fields(self):
        # Create a query
        query = ElasticSearchQuery(models.SearchTest.objects.all(), "Hello", fields=['title'])

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}]}, 'query': {'query_string': {'query': 'Hello', 'fields': ['title']}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_exact_lookup(self):
        # Create a query
        query = ElasticSearchQuery(models.SearchTest.objects.filter(title__exact="Test"), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'and': [{'term': {'title': 'Test'}}]}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_none_lookup(self):
        # Create a query
        query = ElasticSearchQuery(models.SearchTest.objects.filter(title=None), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'and': [{'missing': {'field': 'title'}}]}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_isnull_true_lookup(self):
        # Create a query
        query = ElasticSearchQuery(models.SearchTest.objects.filter(title__isnull=True), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'and': [{'missing': {'field': 'title'}}]}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_isnull_false_lookup(self):
        # Create a query
        query = ElasticSearchQuery(models.SearchTest.objects.filter(title__isnull=False), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'and': [{'not': {'missing': {'field': 'title'}}}]}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_startswith_lookup(self):
        # Create a query
        query = ElasticSearchQuery(models.SearchTest.objects.filter(title__startswith="Test"), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'and': [{'prefix': {'title': 'Test'}}]}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_gt_lookup(self):
        # This shares the same code path as gte, lt and lte so theres no need to test those
        # This also tests conversion of python dates to strings

        # Create a query
        query = ElasticSearchQuery(models.SearchTest.objects.filter(published_date__gt=datetime.datetime(2014, 4, 29)), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'and': [{'range': {'published_date': {'gt': '2014-04-29'}}}]}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_range_lookup(self):
        start_date = datetime.datetime(2014, 4, 29)
        end_date = datetime.datetime(2014, 8, 19)

        # Create a query
        query = ElasticSearchQuery(models.SearchTest.objects.filter(published_date__range=(start_date, end_date)), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'and': [{'range': {'published_date': {'gte': '2014-04-29', 'lte': '2014-08-19'}}}]}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)
