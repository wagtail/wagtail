# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from wagtail.tests.utils import unittest
import datetime
import json

from django.test import TestCase
from django.db.models import Q

from wagtail.tests import models
from .test_backends import BackendTests


class TestElasticSearchBackend(BackendTests, TestCase):
    backend_path = 'wagtail.wagtailsearch.backends.elasticsearch.ElasticSearch'

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
            results = list(self.backend.search("Hello", models.SearchTest, filters=dict(id=42)))

    def test_filter_with_unsupported_lookup_type(self):
        from wagtail.wagtailsearch.backends.base import FilterError

        with self.assertRaises(FilterError):
            results = list(self.backend.search("Hello", models.SearchTest, filters=dict(title__iregex='h(ea)llo')))

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


class TestElasticSearchQuery(TestCase):
    def assertDictEqual(self, a, b):
        default = self.JSONSerializer().default
        self.assertEqual(json.dumps(a, sort_keys=True, default=default), json.dumps(b, sort_keys=True, default=default))

    def setUp(self):
        # Import using a try-catch block to prevent crashes if the elasticsearch-py
        # module is not installed
        try:
            from wagtail.wagtailsearch.backends.elasticsearch import ElasticSearchQuery
            from elasticsearch.serializer import JSONSerializer
        except ImportError:
            raise unittest.SkipTest("elasticsearch-py not installed")

        self.ElasticSearchQuery = ElasticSearchQuery
        self.JSONSerializer = JSONSerializer

    def test_simple(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.all(), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'prefix': {'content_type': 'tests_searchtest'}}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_none_query_string(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.all(), None)

        # Check it
        expected_result = {'filtered': {'filter': {'prefix': {'content_type': 'tests_searchtest'}}, 'query': {'match_all': {}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_filter(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(title="Test"), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'term': {'title_filter': 'Test'}}]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_and_filter(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(title="Test", live=True), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'and': [{'term': {'live_filter': True}}, {'term': {'title_filter': 'Test'}}]}]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}

        # Make sure field filters are sorted (as they can be in any order which may cause false positives)
        query = query.to_es()
        field_filters = query['filtered']['filter']['and'][1]['and']
        field_filters[:] = sorted(field_filters, key=lambda f: list(f['term'].keys())[0])

        self.assertDictEqual(query, expected_result)

    def test_or_filter(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(Q(title="Test") | Q(live=True)), "Hello")

        # Make sure field filters are sorted (as they can be in any order which may cause false positives)
        query = query.to_es()
        field_filters = query['filtered']['filter']['and'][1]['or']
        field_filters[:] = sorted(field_filters, key=lambda f: list(f['term'].keys())[0])

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'or': [{'term': {'live_filter': True}}, {'term': {'title_filter': 'Test'}}]}]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query, expected_result)

    def test_negated_filter(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.exclude(live=True), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'not': {'term': {'live_filter': True}}}]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_fields(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.all(), "Hello", fields=['title'])

        # Check it
        expected_result = {'filtered': {'filter': {'prefix': {'content_type': 'tests_searchtest'}}, 'query': {'match': {'title': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_exact_lookup(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(title__exact="Test"), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'term': {'title_filter': 'Test'}}]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_none_lookup(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(title=None), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'missing': {'field': 'title_filter'}}]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_isnull_true_lookup(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(title__isnull=True), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'missing': {'field': 'title_filter'}}]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_isnull_false_lookup(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(title__isnull=False), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'not': {'missing': {'field': 'title_filter'}}}]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_startswith_lookup(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(title__startswith="Test"), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'prefix': {'title_filter': 'Test'}}]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_gt_lookup(self):
        # This also tests conversion of python dates to strings

        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(published_date__gt=datetime.datetime(2014, 4, 29)), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'range': {'published_date_filter': {'gt': '2014-04-29'}}}]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_lt_lookup(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(published_date__lt=datetime.datetime(2014, 4, 29)), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'range': {'published_date_filter': {'lt': '2014-04-29'}}}]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_gte_lookup(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(published_date__gte=datetime.datetime(2014, 4, 29)), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'range': {'published_date_filter': {'gte': '2014-04-29'}}}]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_lte_lookup(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(published_date__lte=datetime.datetime(2014, 4, 29)), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'range': {'published_date_filter': {'lte': '2014-04-29'}}}]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_range_lookup(self):
        start_date = datetime.datetime(2014, 4, 29)
        end_date = datetime.datetime(2014, 8, 19)

        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(published_date__range=(start_date, end_date)), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'range': {'published_date_filter': {'gte': '2014-04-29', 'lte': '2014-08-19'}}}]}, 'query': {'multi_match': {'query': 'Hello', 'fields': ['_all', '_partials']}}}}
        self.assertDictEqual(query.to_es(), expected_result)


class TestElasticSearchMapping(TestCase):
    def assertDictEqual(self, a, b):
        default = self.JSONSerializer().default
        self.assertEqual(json.dumps(a, sort_keys=True, default=default), json.dumps(b, sort_keys=True, default=default))

    def setUp(self):
        # Import using a try-catch block to prevent crashes if the elasticsearch-py
        # module is not installed
        try:
            from wagtail.wagtailsearch.backends.elasticsearch import ElasticSearchMapping
            from elasticsearch.serializer import JSONSerializer
        except ImportError:
            raise unittest.SkipTest("elasticsearch-py not installed")

        self.JSONSerializer = JSONSerializer

        # Create ES mapping
        self.es_mapping = ElasticSearchMapping(models.SearchTest)

        # Create ES document
        self.obj = models.SearchTest(title="Hello")
        self.obj.save()

    def test_get_document_type(self):
        self.assertEqual(self.es_mapping.get_document_type(), 'tests_searchtest')

    def test_get_mapping(self):
        # Build mapping
        mapping = self.es_mapping.get_mapping()

        # Check
        expected_result = {
            'tests_searchtest': {
                'properties': {
                    'pk': {'index': 'not_analyzed', 'type': 'string', 'store': 'yes', 'include_in_all': False},
                    'content_type': {'index': 'not_analyzed', 'type': 'string', 'include_in_all': False},
                    '_partials': {'index_analyzer': 'edgengram_analyzer', 'include_in_all': False, 'type': 'string'},
                    'live_filter': {'index': 'not_analyzed', 'type': 'boolean', 'include_in_all': False},
                    'published_date_filter': {'index': 'not_analyzed', 'type': 'date', 'include_in_all': False},
                    'title': {'type': 'string', 'include_in_all': True, 'index_analyzer': 'edgengram_analyzer'},
                    'title_filter': {'index': 'not_analyzed', 'type': 'string', 'include_in_all': False},
                    'content': {'type': 'string', 'include_in_all': True},
                    'callable_indexed_field': {'type': 'string', 'include_in_all': True}
                }
            }
        }

        self.assertDictEqual(mapping, expected_result)

    def test_get_document_id(self):
        self.assertEqual(self.es_mapping.get_document_id(self.obj), 'tests_searchtest:' + str(self.obj.pk))

    def test_get_document(self):
        # Get document
        document = self.es_mapping.get_document(self.obj)

        # Check
        expected_result = {
            'pk': str(self.obj.pk),
            'content_type': 'tests_searchtest',
            '_partials': ['Hello'],
            'live_filter': False,
            'published_date_filter': None,
            'title': 'Hello',
            'title_filter': 'Hello',
            'callable_indexed_field': 'Callable',
            'content': '',
        }

        self.assertDictEqual(document, expected_result)


class TestElasticSearchMappingInheritance(TestCase):
    def assertDictEqual(self, a, b):
        default = self.JSONSerializer().default
        self.assertEqual(json.dumps(a, sort_keys=True, default=default), json.dumps(b, sort_keys=True, default=default))

    def setUp(self):
        # Import using a try-catch block to prevent crashes if the elasticsearch-py
        # module is not installed
        try:
            from wagtail.wagtailsearch.backends.elasticsearch import ElasticSearchMapping
            from elasticsearch.serializer import JSONSerializer
        except ImportError:
            raise unittest.SkipTest("elasticsearch-py not installed")

        self.JSONSerializer = JSONSerializer

        # Create ES mapping
        self.es_mapping = ElasticSearchMapping(models.SearchTestChild)

        # Create ES document
        self.obj = models.SearchTestChild(title="Hello", subtitle="World")
        self.obj.save()

    def test_get_document_type(self):
        self.assertEqual(self.es_mapping.get_document_type(), 'tests_searchtest_tests_searchtestchild')

    def test_get_mapping(self):
        # Build mapping
        mapping = self.es_mapping.get_mapping()

        # Check
        expected_result = {
            'tests_searchtest_tests_searchtestchild': {
                'properties': {
                    # New
                    'extra_content': {'type': 'string', 'include_in_all': True},
                    'subtitle': {'type': 'string', 'include_in_all': True, 'index_analyzer': 'edgengram_analyzer'},

                    # Inherited
                    'pk': {'index': 'not_analyzed', 'type': 'string', 'store': 'yes', 'include_in_all': False},
                    'content_type': {'index': 'not_analyzed', 'type': 'string', 'include_in_all': False},
                    '_partials': {'index_analyzer': 'edgengram_analyzer', 'include_in_all': False, 'type': 'string'},
                    'live_filter': {'index': 'not_analyzed', 'type': 'boolean', 'include_in_all': False},
                    'published_date_filter': {'index': 'not_analyzed', 'type': 'date', 'include_in_all': False},
                    'title': {'type': 'string', 'include_in_all': True, 'index_analyzer': 'edgengram_analyzer'},
                    'title_filter': {'index': 'not_analyzed', 'type': 'string', 'include_in_all': False},
                    'content': {'type': 'string', 'include_in_all': True},
                    'callable_indexed_field': {'type': 'string', 'include_in_all': True}
                }
            }
        }

        self.assertDictEqual(mapping, expected_result)

    def test_get_document_id(self):
        # This must be tests_searchtest instead of 'tests_searchtest_tests_searchtestchild'
        # as it uses the contents base content type name.
        # This prevents the same object being accidentally indexed twice.
        self.assertEqual(self.es_mapping.get_document_id(self.obj), 'tests_searchtest:' + str(self.obj.pk))

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

            # Changed
            'content_type': 'tests_searchtest_tests_searchtestchild',

            # Inherited
            'pk': str(self.obj.pk),
            '_partials': ['Hello', 'World'],
            'live_filter': False,
            'published_date_filter': None,
            'title': 'Hello',
            'title_filter': 'Hello',
            'callable_indexed_field': 'Callable',
            'content': '',
        }

        self.assertDictEqual(document, expected_result)


class TestBackendConfiguration(TestCase):
    def setUp(self):
        # Import using a try-catch block to prevent crashes if the elasticsearch-py
        # module is not installed
        try:
            from wagtail.wagtailsearch.backends.elasticsearch import ElasticSearch
        except ImportError:
            raise unittest.SkipTest("elasticsearch-py not installed")

        self.ElasticSearch = ElasticSearch

    def test_default_settings(self):
        backend = self.ElasticSearch(params={})

        self.assertEqual(len(backend.es_hosts), 1)
        self.assertEqual(backend.es_hosts[0]['host'], 'localhost')
        self.assertEqual(backend.es_hosts[0]['port'], 9200)
        self.assertEqual(backend.es_hosts[0]['use_ssl'], False)

    def test_hosts(self):
        # This tests that HOSTS goes to es_hosts
        backend = self.ElasticSearch(params={
            'HOSTS': [
                {
                    'host': '127.0.0.1',
                    'port': 9300,
                    'use_ssl': True,
                }
            ]
        })

        self.assertEqual(len(backend.es_hosts), 1)
        self.assertEqual(backend.es_hosts[0]['host'], '127.0.0.1')
        self.assertEqual(backend.es_hosts[0]['port'], 9300)
        self.assertEqual(backend.es_hosts[0]['use_ssl'], True)

    def test_urls(self):
        # This test backwards compatibility with old URLS setting
        backend = self.ElasticSearch(params={
            'URLS': [
                'http://localhost:12345',
                'https://127.0.0.1:54321',
                'http://username:password@elasticsearch.mysite.com',
                'https://elasticsearch.mysite.com/hello',
            ],
        })

        self.assertEqual(len(backend.es_hosts), 4)
        self.assertEqual(backend.es_hosts[0]['host'], 'localhost')
        self.assertEqual(backend.es_hosts[0]['port'], 12345)
        self.assertEqual(backend.es_hosts[0]['use_ssl'], False)

        self.assertEqual(backend.es_hosts[1]['host'], '127.0.0.1')
        self.assertEqual(backend.es_hosts[1]['port'], 54321)
        self.assertEqual(backend.es_hosts[1]['use_ssl'], True)

        self.assertEqual(backend.es_hosts[2]['host'], 'elasticsearch.mysite.com')
        self.assertEqual(backend.es_hosts[2]['port'], 80)
        self.assertEqual(backend.es_hosts[2]['use_ssl'], False)
        self.assertEqual(backend.es_hosts[2]['http_auth'], ('username', 'password'))

        self.assertEqual(backend.es_hosts[3]['host'], 'elasticsearch.mysite.com')
        self.assertEqual(backend.es_hosts[3]['port'], 443)
        self.assertEqual(backend.es_hosts[3]['use_ssl'], True)
        self.assertEqual(backend.es_hosts[3]['url_prefix'], '/hello')
