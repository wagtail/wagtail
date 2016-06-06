# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import datetime
import json
import os
import time
import unittest

import mock
from django.core import management
from django.db.models import Q
from django.test import TestCase
from django.utils.six import StringIO
from elasticsearch.serializer import JSONSerializer

from wagtail.tests.search import models
from wagtail.wagtailsearch.backends import get_search_backend
from wagtail.wagtailsearch.backends.elasticsearch import ElasticSearch

from .test_backends import BackendTests


class TestElasticSearchBackend(BackendTests, TestCase):
    backend_path = 'wagtail.wagtailsearch.backends.elasticsearch'

    def test_search_with_spaces_only(self):
        # Search for some space characters and hope it doesn't crash
        results = self.backend.search("   ", models.SearchTest)

        # Queries are lazily evaluated, force it to run
        list(results)

        # Didn't crash, yay!

    def test_filter_on_non_filterindex_field(self):
        # id is not listed in the search_fields for SearchTest; this should raise a FieldError
        from wagtail.wagtailsearch.backends.base import FieldError

        with self.assertRaises(FieldError):
            list(self.backend.search("Hello", models.SearchTest, filters=dict(id=42)))

    def test_filter_with_unsupported_lookup_type(self):
        from wagtail.wagtailsearch.backends.base import FilterError

        with self.assertRaises(FilterError):
            list(self.backend.search("Hello", models.SearchTest, filters=dict(title__iregex='h(ea)llo')))

    def test_partial_search(self):
        # Reset the index
        self.backend.reset_index()
        self.backend.add_type(models.SearchTest)
        self.backend.add_type(models.SearchTestChild)

        # Add some test data
        obj = models.SearchTest()
        obj.title = "HelloWorld"
        obj.live = True
        obj.save()
        self.backend.add(obj)

        # Refresh the index
        self.backend.refresh_index()

        # Search and check
        results = self.backend.search("HelloW", models.SearchTest.objects.all())

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, obj.id)

    def test_child_partial_search(self):
        # Reset the index
        self.backend.reset_index()
        self.backend.add_type(models.SearchTest)
        self.backend.add_type(models.SearchTestChild)

        obj = models.SearchTestChild()
        obj.title = "WorldHello"
        obj.subtitle = "HelloWorld"
        obj.live = True
        obj.save()
        self.backend.add(obj)

        # Refresh the index
        self.backend.refresh_index()

        # Search and check
        results = self.backend.search("HelloW", models.SearchTest.objects.all())

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, obj.id)

    def test_ascii_folding(self):
        # Reset the index
        self.backend.reset_index()
        self.backend.add_type(models.SearchTest)
        self.backend.add_type(models.SearchTestChild)

        # Add some test data
        obj = models.SearchTest()
        obj.title = "Ĥéllø"
        obj.live = True
        obj.save()
        self.backend.add(obj)

        # Refresh the index
        self.backend.refresh_index()

        # Search and check
        results = self.backend.search("Hello", models.SearchTest.objects.all())

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, obj.id)

    def test_query_analyser(self):
        """
        This is testing that fields that use edgengram_analyzer as their index analyser do not
        have it also as their query analyser
        """
        # Reset the index
        self.backend.reset_index()
        self.backend.add_type(models.SearchTest)
        self.backend.add_type(models.SearchTestChild)

        # Add some test data
        obj = models.SearchTest()
        obj.title = "Hello"
        obj.live = True
        obj.save()
        self.backend.add(obj)

        # Refresh the index
        self.backend.refresh_index()

        # Test search for "Hello"
        results = self.backend.search("Hello", models.SearchTest.objects.all())

        # Should find the result
        self.assertEqual(len(results), 1)

        # Test search for "Horse"
        results = self.backend.search("Horse", models.SearchTest.objects.all())

        # Even though they both start with the letter "H". This should not be considered a match
        self.assertEqual(len(results), 0)

    def test_search_with_hyphen(self):
        """
        This tests that punctuation characters are treated the same
        way in both indexing and querying.

        See: https://github.com/torchbox/wagtail/issues/937
        """
        # Reset the index
        self.backend.reset_index()
        self.backend.add_type(models.SearchTest)
        self.backend.add_type(models.SearchTestChild)

        # Add some test data
        obj = models.SearchTest()
        obj.title = "Hello-World"
        obj.live = True
        obj.save()
        self.backend.add(obj)

        # Refresh the index
        self.backend.refresh_index()

        # Test search for "Hello-World"
        results = self.backend.search("Hello-World", models.SearchTest.objects.all())

        # Should find the result
        self.assertEqual(len(results), 1)

    def test_custom_ordering(self):
        # Reset the index
        self.backend.reset_index()
        self.backend.add_type(models.SearchTest)

        # Add some test data
        # a is more relevant, but b is more recent
        a = models.SearchTest()
        a.title = "Hello Hello World"
        a.live = True
        a.published_date = datetime.date(2015, 10, 11)
        a.save()
        self.backend.add(a)

        b = models.SearchTest()
        b.title = "Hello World"
        b.live = True
        b.published_date = datetime.date(2015, 10, 12)
        b.save()
        self.backend.add(b)

        # Refresh the index
        self.backend.refresh_index()

        # Do a search ordered by relevence
        results = self.backend.search("Hello", models.SearchTest.objects.all())
        self.assertEqual(list(results), [a, b])

        # Do a search ordered by published date
        results = self.backend.search(
            "Hello", models.SearchTest.objects.order_by('-published_date'), order_by_relevance=False
        )
        self.assertEqual(list(results), [b, a])

    def test_and_operator_with_single_field(self):
        # Testing for bug #1859

        # Reset the index
        self.backend.reset_index()
        self.backend.add_type(models.SearchTest)

        a = models.SearchTest()
        a.title = "Hello World"
        a.live = True
        a.published_date = datetime.date(2015, 10, 12)
        a.save()
        self.backend.add(a)

        # Refresh the index
        self.backend.refresh_index()

        # Run query with "and" operator and single field
        results = self.backend.search("Hello World", models.SearchTest, operator='and', fields=['title'])
        self.assertEqual(list(results), [a])

    def test_update_index_command_schema_only(self):
        # Reset the index, this should clear out the index
        self.backend.reset_index()

        # Give Elasticsearch some time to catch up...
        time.sleep(1)

        results = self.backend.search(None, models.SearchTest)
        self.assertEqual(set(results), set())

        # Run update_index command
        with self.ignore_deprecation_warnings():
            # ignore any DeprecationWarnings thrown by models with old-style indexed_fields definitions
            management.call_command(
                'update_index', backend_name=self.backend_name, schema_only=True, interactive=False, stdout=StringIO()
            )

        # Unlike the test_update_index_command test. This should not give any results
        results = self.backend.search(None, models.SearchTest)
        self.assertEqual(set(results), set())


class TestElasticSearchQuery(TestCase):
    def assertDictEqual(self, a, b):
        default = JSONSerializer().default
        self.assertEqual(
            json.dumps(a, sort_keys=True, default=default), json.dumps(b, sort_keys=True, default=default)
        )

    query_class = ElasticSearch.query_class

    def test_simple(self):
        # Create a query
        query = self.query_class(models.SearchTest.objects.all(), "Hello")

        # Check it
        expected_result = {'filtered': {
            'filter': {'prefix': {'content_type': 'searchtests_searchtest'}},
            'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}
        }}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_none_query_string(self):
        # Create a query
        query = self.query_class(models.SearchTest.objects.all(), None)

        # Check it
        expected_result = {'filtered': {
            'filter': {'prefix': {'content_type': 'searchtests_searchtest'}},
            'query': {'match_all': {}}
        }}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_and_operator(self):
        # Create a query
        query = self.query_class(models.SearchTest.objects.all(), "Hello", operator='and')

        # Check it
        expected_result = {'filtered': {
            'filter': {'prefix': {'content_type': 'searchtests_searchtest'}},
            'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials'], 'operator': 'and'}}
        }}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_filter(self):
        # Create a query
        query = self.query_class(models.SearchTest.objects.filter(title="Test"), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [
            {'prefix': {'content_type': 'searchtests_searchtest'}},
            {'term': {'title_filter': 'Test'}}
        ]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_and_filter(self):
        # Create a query
        query = self.query_class(models.SearchTest.objects.filter(title="Test", live=True), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [
            {'prefix': {'content_type': 'searchtests_searchtest'}},
            {'and': [{'term': {'live_filter': True}}, {'term': {'title_filter': 'Test'}}]}
        ]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}

        # Make sure field filters are sorted (as they can be in any order which may cause false positives)
        query = query.get_query()
        field_filters = query['filtered']['filter']['and'][1]['and']
        field_filters[:] = sorted(field_filters, key=lambda f: list(f['term'].keys())[0])

        self.assertDictEqual(query, expected_result)

    def test_or_filter(self):
        # Create a query
        query = self.query_class(models.SearchTest.objects.filter(Q(title="Test") | Q(live=True)), "Hello")

        # Make sure field filters are sorted (as they can be in any order which may cause false positives)
        query = query.get_query()
        field_filters = query['filtered']['filter']['and'][1]['or']
        field_filters[:] = sorted(field_filters, key=lambda f: list(f['term'].keys())[0])

        # Check it
        expected_result = {'filtered': {'filter': {'and': [
            {'prefix': {'content_type': 'searchtests_searchtest'}},
            {'or': [{'term': {'live_filter': True}}, {'term': {'title_filter': 'Test'}}]}
        ]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query, expected_result)

    def test_negated_filter(self):
        # Create a query
        query = self.query_class(models.SearchTest.objects.exclude(live=True), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [
            {'prefix': {'content_type': 'searchtests_searchtest'}},
            {'not': {'term': {'live_filter': True}}}
        ]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_fields(self):
        # Create a query
        query = self.query_class(models.SearchTest.objects.all(), "Hello", fields=['title'])

        # Check it
        expected_result = {'filtered': {
            'filter': {'prefix': {'content_type': 'searchtests_searchtest'}},
            'query': {'match': {'title': 'Hello'}}
        }}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_fields_with_and_operator(self):
        # Create a query
        query = self.query_class(models.SearchTest.objects.all(), "Hello", fields=['title'], operator='and')

        # Check it
        expected_result = {'filtered': {
            'filter': {'prefix': {'content_type': 'searchtests_searchtest'}},
            'query': {'match': {'title': {'query': 'Hello', 'operator': 'and'}}}
        }}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_multiple_fields(self):
        # Create a query
        query = self.query_class(models.SearchTest.objects.all(), "Hello", fields=['title', 'content'])

        # Check it
        expected_result = {'filtered': {
            'filter': {'prefix': {'content_type': 'searchtests_searchtest'}},
            'query': {'multi_match': {'fields': ['title', 'content'], 'query': 'Hello'}}
        }}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_multiple_fields_with_and_operator(self):
        # Create a query
        query = self.query_class(
            models.SearchTest.objects.all(), "Hello", fields=['title', 'content'], operator='and'
        )

        # Check it
        expected_result = {'filtered': {
            'filter': {'prefix': {'content_type': 'searchtests_searchtest'}},
            'query': {'multi_match': {'fields': ['title', 'content'], 'query': 'Hello', 'operator': 'and'}}
        }}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_exact_lookup(self):
        # Create a query
        query = self.query_class(models.SearchTest.objects.filter(title__exact="Test"), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [
            {'prefix': {'content_type': 'searchtests_searchtest'}},
            {'term': {'title_filter': 'Test'}}
        ]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_none_lookup(self):
        # Create a query
        query = self.query_class(models.SearchTest.objects.filter(title=None), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [
            {'prefix': {'content_type': 'searchtests_searchtest'}},
            {'missing': {'field': 'title_filter'}}
        ]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_isnull_true_lookup(self):
        # Create a query
        query = self.query_class(models.SearchTest.objects.filter(title__isnull=True), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [
            {'prefix': {'content_type': 'searchtests_searchtest'}},
            {'missing': {'field': 'title_filter'}}
        ]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_isnull_false_lookup(self):
        # Create a query
        query = self.query_class(models.SearchTest.objects.filter(title__isnull=False), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [
            {'prefix': {'content_type': 'searchtests_searchtest'}},
            {'not': {'missing': {'field': 'title_filter'}}}
        ]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_startswith_lookup(self):
        # Create a query
        query = self.query_class(models.SearchTest.objects.filter(title__startswith="Test"), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [
            {'prefix': {'content_type': 'searchtests_searchtest'}},
            {'prefix': {'title_filter': 'Test'}}
        ]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_gt_lookup(self):
        # This also tests conversion of python dates to strings

        # Create a query
        query = self.query_class(
            models.SearchTest.objects.filter(published_date__gt=datetime.datetime(2014, 4, 29)), "Hello"
        )

        # Check it
        expected_result = {'filtered': {'filter': {'and': [
            {'prefix': {'content_type': 'searchtests_searchtest'}},
            {'range': {'published_date_filter': {'gt': '2014-04-29'}}}
        ]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_lt_lookup(self):
        # Create a query
        query = self.query_class(
            models.SearchTest.objects.filter(published_date__lt=datetime.datetime(2014, 4, 29)), "Hello"
        )

        # Check it
        expected_result = {'filtered': {'filter': {'and': [
            {'prefix': {'content_type': 'searchtests_searchtest'}},
            {'range': {'published_date_filter': {'lt': '2014-04-29'}}}
        ]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_gte_lookup(self):
        # Create a query
        query = self.query_class(
            models.SearchTest.objects.filter(published_date__gte=datetime.datetime(2014, 4, 29)), "Hello"
        )

        # Check it
        expected_result = {'filtered': {'filter': {'and': [
            {'prefix': {'content_type': 'searchtests_searchtest'}},
            {'range': {'published_date_filter': {'gte': '2014-04-29'}}}
        ]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_lte_lookup(self):
        # Create a query
        query = self.query_class(
            models.SearchTest.objects.filter(published_date__lte=datetime.datetime(2014, 4, 29)), "Hello"
        )

        # Check it
        expected_result = {'filtered': {'filter': {'and': [
            {'prefix': {'content_type': 'searchtests_searchtest'}},
            {'range': {'published_date_filter': {'lte': '2014-04-29'}}}
        ]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_range_lookup(self):
        start_date = datetime.datetime(2014, 4, 29)
        end_date = datetime.datetime(2014, 8, 19)

        # Create a query
        query = self.query_class(
            models.SearchTest.objects.filter(published_date__range=(start_date, end_date)), "Hello"
        )

        # Check it
        expected_result = {'filtered': {'filter': {'and': [
            {'prefix': {'content_type': 'searchtests_searchtest'}},
            {'range': {'published_date_filter': {'gte': '2014-04-29', 'lte': '2014-08-19'}}}
        ]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.get_query(), expected_result)

    def test_custom_ordering(self):
        # Create a query
        query = self.query_class(
            models.SearchTest.objects.order_by('published_date'), "Hello", order_by_relevance=False
        )

        # Check it
        expected_result = [{'published_date_filter': 'asc'}]
        self.assertDictEqual(query.get_sort(), expected_result)

    def test_custom_ordering_reversed(self):
        # Create a query
        query = self.query_class(
            models.SearchTest.objects.order_by('-published_date'), "Hello", order_by_relevance=False
        )

        # Check it
        expected_result = [{'published_date_filter': 'desc'}]
        self.assertDictEqual(query.get_sort(), expected_result)

    def test_custom_ordering_multiple(self):
        # Create a query
        query = self.query_class(
            models.SearchTest.objects.order_by('published_date', 'live'), "Hello", order_by_relevance=False
        )

        # Check it
        expected_result = [{'published_date_filter': 'asc'}, {'live_filter': 'asc'}]
        self.assertDictEqual(query.get_sort(), expected_result)


class TestElasticSearchResults(TestCase):
    def assertDictEqual(self, a, b):
        default = JSONSerializer().default
        self.assertEqual(
            json.dumps(a, sort_keys=True, default=default), json.dumps
        )

    def setUp(self):
        self.objects = []

        for i in range(3):
            self.objects.append(models.SearchTest.objects.create(title=str(i)))

    def get_results(self):
        backend = ElasticSearch({})
        query = mock.MagicMock()
        query.queryset = models.SearchTest.objects.all()
        query.get_query.return_value = 'QUERY'
        query.get_sort.return_value = None
        return backend.results_class(backend, query)

    def construct_search_response(self, results):
        return {
            '_shards': {'failed': 0, 'successful': 5, 'total': 5},
            'hits': {
                'hits': [
                    {
                        '_id': 'searchtests_searchtest:' + str(result),
                        '_index': 'wagtail',
                        '_score': 1,
                        '_type': 'searchtests_searchtest',
                        'fields': {
                            'pk': [str(result)],
                        }
                    }
                    for result in results
                ],
                'max_score': 1,
                'total': len(results)
            },
            'timed_out': False,
            'took': 2
        }

    @mock.patch('elasticsearch.Elasticsearch.search')
    def test_basic_search(self, search):
        search.return_value = self.construct_search_response([])
        results = self.get_results()

        list(results)  # Performs search

        search.assert_any_call(
            from_=0,
            body={'query': 'QUERY'},
            _source=False,
            fields='pk',
            index='wagtail'
        )

    @mock.patch('elasticsearch.Elasticsearch.search')
    def test_get_single_item(self, search):
        # Need to return something to prevent index error
        search.return_value = self.construct_search_response([self.objects[0].id])
        results = self.get_results()

        results[10]  # Performs search

        search.assert_any_call(
            from_=10,
            body={'query': 'QUERY'},
            _source=False,
            fields='pk',
            index='wagtail',
            size=1
        )

    @mock.patch('elasticsearch.Elasticsearch.search')
    def test_slice_results(self, search):
        search.return_value = self.construct_search_response([])
        results = self.get_results()[1:4]

        list(results)  # Performs search

        search.assert_any_call(
            from_=1,
            body={'query': 'QUERY'},
            _source=False,
            fields='pk',
            index='wagtail',
            size=3
        )

    @mock.patch('elasticsearch.Elasticsearch.search')
    def test_slice_results_multiple_times(self, search):
        search.return_value = self.construct_search_response([])
        results = self.get_results()[10:][:10]

        list(results)  # Performs search

        search.assert_any_call(
            from_=10,
            body={'query': 'QUERY'},
            _source=False,
            fields='pk',
            index='wagtail',
            size=10
        )

    @mock.patch('elasticsearch.Elasticsearch.search')
    def test_slice_results_and_get_item(self, search):
        # Need to return something to prevent index error
        search.return_value = self.construct_search_response([self.objects[0].id])
        results = self.get_results()[10:]

        results[10]  # Performs search

        search.assert_any_call(
            from_=20,
            body={'query': 'QUERY'},
            _source=False,
            fields='pk',
            index='wagtail',
            size=1
        )

    @mock.patch('elasticsearch.Elasticsearch.search')
    def test_result_returned(self, search):
        search.return_value = self.construct_search_response([self.objects[0].id])
        results = self.get_results()

        self.assertEqual(results[0], self.objects[0])

    @mock.patch('elasticsearch.Elasticsearch.search')
    def test_len_1(self, search):
        search.return_value = self.construct_search_response([self.objects[0].id])
        results = self.get_results()

        self.assertEqual(len(results), 1)

    @mock.patch('elasticsearch.Elasticsearch.search')
    def test_len_2(self, search):
        search.return_value = self.construct_search_response([self.objects[0].id, self.objects[1].id])
        results = self.get_results()

        self.assertEqual(len(results), 2)

    @mock.patch('elasticsearch.Elasticsearch.search')
    def test_duplicate_results(self, search):  # Duplicates will not be removed
        search.return_value = self.construct_search_response([self.objects[0].id, self.objects[0].id])
        results = list(self.get_results())  # Must cast to list so we only create one query

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], self.objects[0])
        self.assertEqual(results[1], self.objects[0])

    @mock.patch('elasticsearch.Elasticsearch.search')
    def test_result_order(self, search):
        search.return_value = self.construct_search_response(
            [self.objects[0].id, self.objects[1].id, self.objects[2].id]
        )
        results = list(self.get_results())  # Must cast to list so we only create one query

        self.assertEqual(results[0], self.objects[0])
        self.assertEqual(results[1], self.objects[1])
        self.assertEqual(results[2], self.objects[2])

    @mock.patch('elasticsearch.Elasticsearch.search')
    def test_result_order_2(self, search):
        search.return_value = self.construct_search_response(
            [self.objects[2].id, self.objects[1].id, self.objects[0].id]
        )
        results = list(self.get_results())  # Must cast to list so we only create one query

        self.assertEqual(results[0], self.objects[2])
        self.assertEqual(results[1], self.objects[1])
        self.assertEqual(results[2], self.objects[0])


class TestElasticSearchMapping(TestCase):
    def assertDictEqual(self, a, b):
        default = JSONSerializer().default
        self.assertEqual(
            json.dumps(a, sort_keys=True, default=default), json.dumps(b, sort_keys=True, default=default)
        )

    def setUp(self):
        # Create ES mapping
        self.es_mapping = ElasticSearch.mapping_class(models.SearchTest)

        # Create ES document
        self.obj = models.SearchTest(title="Hello")
        self.obj.save()
        self.obj.tags.add("a tag")

    def test_get_document_type(self):
        self.assertEqual(self.es_mapping.get_document_type(), 'searchtests_searchtest')

    def test_get_mapping(self):
        # Build mapping
        mapping = self.es_mapping.get_mapping()

        # Check
        expected_result = {
            'searchtests_searchtest': {
                'properties': {
                    'pk': {'index': 'not_analyzed', 'type': 'string', 'store': 'yes', 'include_in_all': False},
                    'content_type': {'index': 'not_analyzed', 'type': 'string', 'include_in_all': False},
                    '_partials': {'index_analyzer': 'edgengram_analyzer', 'include_in_all': False, 'type': 'string'},
                    'live_filter': {'index': 'not_analyzed', 'type': 'boolean', 'include_in_all': False},
                    'published_date_filter': {'index': 'not_analyzed', 'type': 'date', 'include_in_all': False},
                    'title': {'type': 'string', 'include_in_all': True, 'index_analyzer': 'edgengram_analyzer'},
                    'title_filter': {'index': 'not_analyzed', 'type': 'string', 'include_in_all': False},
                    'content': {'type': 'string', 'include_in_all': True},
                    'callable_indexed_field': {'type': 'string', 'include_in_all': True},
                    'tags': {
                        'type': 'nested',
                        'properties': {
                            'name': {'type': 'string', 'include_in_all': True, 'index_analyzer': 'edgengram_analyzer'},
                            'slug_filter': {'index': 'not_analyzed', 'type': 'string', 'include_in_all': False},
                        }
                    },
                }
            }
        }

        self.assertDictEqual(mapping, expected_result)

    def test_get_document_id(self):
        self.assertEqual(self.es_mapping.get_document_id(self.obj), 'searchtests_searchtest:' + str(self.obj.pk))

    def test_get_document(self):
        # Get document
        document = self.es_mapping.get_document(self.obj)

        # Sort partials
        if '_partials' in document:
            document['_partials'].sort()

        # Check
        expected_result = {
            'pk': str(self.obj.pk),
            'content_type': 'searchtests_searchtest',
            '_partials': ['Hello', 'a tag'],
            'live_filter': False,
            'published_date_filter': None,
            'title': 'Hello',
            'title_filter': 'Hello',
            'callable_indexed_field': 'Callable',
            'content': '',
            'tags': [
                {
                    'name': 'a tag',
                    'slug_filter': 'a-tag',
                }
            ],
        }

        self.assertDictEqual(document, expected_result)


class TestElasticSearchMappingInheritance(TestCase):
    def assertDictEqual(self, a, b):
        default = JSONSerializer().default
        self.assertEqual(
            json.dumps(a, sort_keys=True, default=default), json.dumps(b, sort_keys=True, default=default)
        )

    def setUp(self):
        # Create ES mapping
        self.es_mapping = ElasticSearch.mapping_class(models.SearchTestChild)

        # Create ES document
        self.obj = models.SearchTestChild(title="Hello", subtitle="World", page_id=1)
        self.obj.save()
        self.obj.tags.add("a tag")

    def test_get_document_type(self):
        self.assertEqual(self.es_mapping.get_document_type(), 'searchtests_searchtest_searchtests_searchtestchild')

    def test_get_mapping(self):
        # Build mapping
        mapping = self.es_mapping.get_mapping()

        # Check
        expected_result = {
            'searchtests_searchtest_searchtests_searchtestchild': {
                'properties': {
                    # New
                    'extra_content': {'type': 'string', 'include_in_all': True},
                    'subtitle': {'type': 'string', 'include_in_all': True, 'index_analyzer': 'edgengram_analyzer'},
                    'page': {
                        'type': 'nested',
                        'properties': {
                            'title': {'type': 'string', 'include_in_all': True, 'index_analyzer': 'edgengram_analyzer'},
                            'search_description': {'type': 'string', 'include_in_all': True},
                            'live_filter': {'index': 'not_analyzed', 'type': 'boolean', 'include_in_all': False},
                        }
                    },

                    # Inherited
                    'pk': {'index': 'not_analyzed', 'type': 'string', 'store': 'yes', 'include_in_all': False},
                    'content_type': {'index': 'not_analyzed', 'type': 'string', 'include_in_all': False},
                    '_partials': {'index_analyzer': 'edgengram_analyzer', 'include_in_all': False, 'type': 'string'},
                    'live_filter': {'index': 'not_analyzed', 'type': 'boolean', 'include_in_all': False},
                    'published_date_filter': {'index': 'not_analyzed', 'type': 'date', 'include_in_all': False},
                    'title': {'type': 'string', 'include_in_all': True, 'index_analyzer': 'edgengram_analyzer'},
                    'title_filter': {'index': 'not_analyzed', 'type': 'string', 'include_in_all': False},
                    'content': {'type': 'string', 'include_in_all': True},
                    'callable_indexed_field': {'type': 'string', 'include_in_all': True},
                    'tags': {
                        'type': 'nested',
                        'properties': {
                            'name': {'type': 'string', 'include_in_all': True, 'index_analyzer': 'edgengram_analyzer'},
                            'slug_filter': {'index': 'not_analyzed', 'type': 'string', 'include_in_all': False},
                        }
                    },
                }
            }
        }

        self.assertDictEqual(mapping, expected_result)

    def test_get_document_id(self):
        # This must be tests_searchtest instead of 'tests_searchtest_tests_searchtestchild'
        # as it uses the contents base content type name.
        # This prevents the same object being accidentally indexed twice.
        self.assertEqual(self.es_mapping.get_document_id(self.obj), 'searchtests_searchtest:' + str(self.obj.pk))

    def test_get_document(self):
        # Build document
        document = self.es_mapping.get_document(self.obj)

        # Sort partials
        if '_partials' in document:
            document['_partials'].sort()

        # Check
        expected_result = {
            # New
            'extra_content': '',
            'subtitle': 'World',
            'page': {
                'title': 'Root',
                'search_description': '',
                'live_filter': True,
            },

            # Changed
            'content_type': 'searchtests_searchtest_searchtests_searchtestchild',

            # Inherited
            'pk': str(self.obj.pk),
            '_partials': ['Hello', 'Root', 'World', 'a tag'],
            'live_filter': False,
            'published_date_filter': None,
            'title': 'Hello',
            'title_filter': 'Hello',
            'callable_indexed_field': 'Callable',
            'content': '',
            'tags': [
                {
                    'name': 'a tag',
                    'slug_filter': 'a-tag',
                }
            ],
        }

        self.assertDictEqual(document, expected_result)


class TestBackendConfiguration(TestCase):
    def test_default_settings(self):
        backend = ElasticSearch(params={})

        self.assertEqual(len(backend.hosts), 1)
        self.assertEqual(backend.hosts[0]['host'], 'localhost')
        self.assertEqual(backend.hosts[0]['port'], 9200)
        self.assertEqual(backend.hosts[0]['use_ssl'], False)

    def test_hosts(self):
        # This tests that HOSTS goes to es_hosts
        backend = ElasticSearch(params={
            'HOSTS': [
                {
                    'host': '127.0.0.1',
                    'port': 9300,
                    'use_ssl': True,
                    'verify_certs': True,
                }
            ]
        })

        self.assertEqual(len(backend.hosts), 1)
        self.assertEqual(backend.hosts[0]['host'], '127.0.0.1')
        self.assertEqual(backend.hosts[0]['port'], 9300)
        self.assertEqual(backend.hosts[0]['use_ssl'], True)

    def test_urls(self):
        # This test backwards compatibility with old URLS setting
        backend = ElasticSearch(params={
            'URLS': [
                'http://localhost:12345',
                'https://127.0.0.1:54321',
                'http://username:password@elasticsearch.mysite.com',
                'https://elasticsearch.mysite.com/hello',
            ],
        })

        self.assertEqual(len(backend.hosts), 4)
        self.assertEqual(backend.hosts[0]['host'], 'localhost')
        self.assertEqual(backend.hosts[0]['port'], 12345)
        self.assertEqual(backend.hosts[0]['use_ssl'], False)

        self.assertEqual(backend.hosts[1]['host'], '127.0.0.1')
        self.assertEqual(backend.hosts[1]['port'], 54321)
        self.assertEqual(backend.hosts[1]['use_ssl'], True)

        self.assertEqual(backend.hosts[2]['host'], 'elasticsearch.mysite.com')
        self.assertEqual(backend.hosts[2]['port'], 80)
        self.assertEqual(backend.hosts[2]['use_ssl'], False)
        self.assertEqual(backend.hosts[2]['http_auth'], ('username', 'password'))

        self.assertEqual(backend.hosts[3]['host'], 'elasticsearch.mysite.com')
        self.assertEqual(backend.hosts[3]['port'], 443)
        self.assertEqual(backend.hosts[3]['use_ssl'], True)
        self.assertEqual(backend.hosts[3]['url_prefix'], '/hello')


@unittest.skipUnless(os.environ.get('ELASTICSEARCH_URL', False), "ELASTICSEARCH_URL not set")
class TestRebuilder(TestCase):
    def assertDictEqual(self, a, b):
        default = JSONSerializer().default
        self.assertEqual(
            json.dumps(a, sort_keys=True, default=default), json.dumps(b, sort_keys=True, default=default)
        )

    def setUp(self):
        self.backend = get_search_backend('elasticsearch')
        self.es = self.backend.es
        self.rebuilder = self.backend.get_rebuilder()

        self.backend.reset_index()

    def test_start_creates_index(self):
        # First, make sure the index is deleted
        try:
            self.es.indices.delete(self.backend.index_name)
        except self.NotFoundError:
            pass

        self.assertFalse(self.es.indices.exists(self.backend.index_name))

        # Run start
        self.rebuilder.start()

        # Check the index exists
        self.assertTrue(self.es.indices.exists(self.backend.index_name))

    def test_start_deletes_existing_index(self):
        # Put an alias into the index so we can check it was deleted
        self.es.indices.put_alias(name='this_index_should_be_deleted', index=self.backend.index_name)
        self.assertTrue(
            self.es.indices.exists_alias(name='this_index_should_be_deleted', index=self.backend.index_name)
        )

        # Run start
        self.rebuilder.start()

        # The alias should be gone (proving the index was deleted and recreated)
        self.assertFalse(
            self.es.indices.exists_alias(name='this_index_should_be_deleted', index=self.backend.index_name)
        )


@unittest.skipUnless(os.environ.get('ELASTICSEARCH_URL', False), "ELASTICSEARCH_URL not set")
class TestAtomicRebuilder(TestCase):
    def setUp(self):
        self.backend = get_search_backend('elasticsearch')
        self.backend.rebuilder_class = self.backend.atomic_rebuilder_class
        self.es = self.backend.es
        self.rebuilder = self.backend.get_rebuilder()

        self.backend.reset_index()

    def test_start_creates_new_index(self):
        # Rebuilder should make up a new index name that doesn't currently exist
        self.assertFalse(self.es.indices.exists(self.rebuilder.index.name))

        # Run start
        self.rebuilder.start()

        # Check the index exists
        self.assertTrue(self.es.indices.exists(self.rebuilder.index.name))

    def test_start_doesnt_delete_current_index(self):
        # Get current index name
        current_index_name = list(self.es.indices.get_alias(name=self.rebuilder.alias.name).keys())[0]

        # Run start
        self.rebuilder.start()

        # The index should still exist
        self.assertTrue(self.es.indices.exists(current_index_name))

        # And the alias should still point to it
        self.assertTrue(self.es.indices.exists_alias(name=self.rebuilder.alias.name, index=current_index_name))

    def test_finish_updates_alias(self):
        # Run start
        self.rebuilder.start()

        # Check that the alias doesn't point to new index
        self.assertFalse(
            self.es.indices.exists_alias(name=self.rebuilder.alias.name, index=self.rebuilder.index.name)
        )

        # Run finish
        self.rebuilder.finish()

        # Check that the alias now points to the new index
        self.assertTrue(self.es.indices.exists_alias(name=self.rebuilder.alias.name, index=self.rebuilder.index.name))

    def test_finish_deletes_old_index(self):
        # Get current index name
        current_index_name = list(self.es.indices.get_alias(name=self.rebuilder.alias.name).keys())[0]

        # Run start
        self.rebuilder.start()

        # Index should still exist
        self.assertTrue(self.es.indices.exists(current_index_name))

        # Run finish
        self.rebuilder.finish()

        # Index should be gone
        self.assertFalse(self.es.indices.exists(current_index_name))
