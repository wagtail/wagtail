import unittest2 as unittest
import json
import datetime

from django.test import TestCase
from django.db.models import Q

from . import models
from .test_backends import BackendTests


class TestElasticSearchBackend(BackendTests, TestCase):
    backend_path = 'wagtail.wagtailsearch.backends.elasticsearch.ElasticSearch'


class TestElasticSearchQuery(TestCase):
    def assertDictEqual(self, a, b):
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def setUp(self):
        # Import using a try-catch block to prevent crashes if the elasticsearch-py
        # module is not installed
        try:
            from wagtail.wagtailsearch.backends.elasticsearch import ElasticSearchQuery
        except ImportError:
            raise unittest.SkipTest("elasticsearch-py not installed")

        self.ElasticSearchQuery = ElasticSearchQuery

    def test_simple(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.all(), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'prefix': {'content_type': 'tests_searchtest'}}, 'query': {'query_string': {'query': 'Hello'}}}}
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
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'term': {'title_filter': 'Test'}}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_and_filter(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(title="Test", live=True), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'and': [{'term': {'live_filter': True}}, {'term': {'title_filter': 'Test'}}]}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_or_filter(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(Q(title="Test") | Q(live=True)), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'or': [{'term': {'title_filter': 'Test'}}, {'term': {'live_filter': True}}]}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_negated_filter(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.exclude(live=True), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'not': {'term': {'live_filter': True}}}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_fields(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.all(), "Hello", fields=['title'])

        # Check it
        expected_result = {'filtered': {'filter': {'prefix': {'content_type': 'tests_searchtest'}}, 'query': {'query_string': {'query': 'Hello', 'fields': ['title']}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_exact_lookup(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(title__exact="Test"), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'term': {'title_filter': 'Test'}}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_none_lookup(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(title=None), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'missing': {'field': 'title_filter'}}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_isnull_true_lookup(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(title__isnull=True), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'missing': {'field': 'title_filter'}}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_isnull_false_lookup(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(title__isnull=False), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'not': {'missing': {'field': 'title_filter'}}}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_startswith_lookup(self):
        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(title__startswith="Test"), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'prefix': {'title_filter': 'Test'}}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_gt_lookup(self):
        # This shares the same code path as gte, lt and lte so theres no need to test those
        # This also tests conversion of python dates to strings

        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(published_date__gt=datetime.datetime(2014, 4, 29)), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'range': {'published_date_filter': {'gt': '2014-04-29'}}}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)

    def test_range_lookup(self):
        start_date = datetime.datetime(2014, 4, 29)
        end_date = datetime.datetime(2014, 8, 19)

        # Create a query
        query = self.ElasticSearchQuery(models.SearchTest.objects.filter(published_date__range=(start_date, end_date)), "Hello")

        # Check it
        expected_result = {'filtered': {'filter': {'and': [{'prefix': {'content_type': 'tests_searchtest'}}, {'range': {'published_date_filter': {'gte': '2014-04-29', 'lte': '2014-08-19'}}}]}, 'query': {'query_string': {'query': 'Hello'}}}}
        self.assertDictEqual(query.to_es(), expected_result)


class TestElasticSearchType(TestCase):
    """
    This tests that the ElasticSearchType class is doing its job.
    """
    def assertDictEqual(self, a, b):
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def setUp(self):
        # Import using a try-catch block to prevent crashes if the elasticsearch-py
        # module is not installed
        try:
            from wagtail.wagtailsearch.backends.elasticsearch import ElasticSearchType
        except ImportError:
            raise unittest.SkipTest("elasticsearch-py not installed")

        # Create ES type
        self.es_type = ElasticSearchType(models.SearchTest)

    def test_get_doc_type(self):
        self.assertEqual(self.es_type.get_doc_type(), 'tests_searchtest')

    def test_get_mapping(self):
        # Build mapping
        mapping = self.es_type.get_mapping()

        # Check
        expected_result = {
            'tests_searchtest': {
                'properties': {
                    'pk': {'index': 'not_analyzed', 'type': 'string', 'store': 'yes'},
                    'id_filter': {'index': 'not_analyzed', 'type': 'integer'},
                    'content_type': {'index': 'not_analyzed', 'type': 'string'},
                    'live_filter': {'index': 'not_analyzed', 'type': 'boolean'},
                    'published_date_filter': {'index': 'not_analyzed', 'type': 'date'},
                    'title': {'type': 'string'},
                    'title_filter': {'index': 'not_analyzed', 'type': 'string'},
                    'content': {'type': 'string'},
                    'callable_indexed_field': {'type': 'string'}
                }
            }
        }

        self.assertDictEqual(mapping, expected_result)


class TestElasticSearchTypeInheritance(TestCase):
    """
    This tests that the ElasticSearchType class works well with model inheritance.
    """
    def assertDictEqual(self, a, b):
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def setUp(self):
        # Import using a try-catch block to prevent crashes if the elasticsearch-py
        # module is not installed
        try:
            from wagtail.wagtailsearch.backends.elasticsearch import ElasticSearchType
        except ImportError:
            raise unittest.SkipTest("elasticsearch-py not installed")

        # Create ES type
        self.es_type = ElasticSearchType(models.SearchTestChild)

    def test_get_doc_type(self):
        self.assertEqual(self.es_type.get_doc_type(), 'tests_searchtest_tests_searchtestchild')

    def test_get_mapping(self):
        # Build mapping
        mapping = self.es_type.get_mapping()

        # Check
        expected_result = {
            'tests_searchtest_tests_searchtestchild': {
                'properties': {
                    # New
                    'extra_content': {'type': 'string'},
                    'searchtest_ptr_id_filter': {'index': 'not_analyzed', 'type': 'string'},

                    # Inherited
                    'pk': {'index': 'not_analyzed', 'type': 'string', 'store': 'yes'},
                    'content_type': {'index': 'not_analyzed', 'type': 'string'},
                    'live_filter': {'index': 'not_analyzed', 'type': 'boolean'},
                    'published_date_filter': {'index': 'not_analyzed', 'type': 'date'},
                    'title': {'type': 'string'},
                    'title_filter': {'index': 'not_analyzed', 'type': 'string'},
                    'content': {'type': 'string'},
                    'callable_indexed_field': {'type': 'string'}
                }
            }
        }

        self.assertDictEqual(mapping, expected_result)


class TestElasticSearchDocument(TestCase):
    """
    This tests that the ElasticSearchDocument class is doing its job.
    """
    def assertDictEqual(self, a, b):
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def setUp(self):
        # Import using a try-catch block to prevent crashes if the elasticsearch-py
        # module is not installed
        try:
            from wagtail.wagtailsearch.backends.elasticsearch import ElasticSearchDocument
        except ImportError:
            raise unittest.SkipTest("elasticsearch-py not installed")

        # Create ES document
        self.obj = models.SearchTest(title="Hello")
        self.obj.save()
        self.es_doc = ElasticSearchDocument(self.obj)

    def test_get_id(self):
        self.assertEqual(self.es_doc.get_id(), 'tests_searchtest:' + str(self.obj.pk))

    def test_build_document(self):
        # Build document
        document = self.es_doc.build_document()

        # Check
        expected_result = {
            'pk': str(self.obj.pk),
            'content_type': 'tests_searchtest',
            'id': 'tests_searchtest:' + str(self.obj.pk),
            'id_filter': self.obj.pk,
            'live_filter': False,
            'published_date_filter': None,
            'title': 'Hello',
            'title_filter': 'Hello',
            'callable_indexed_field': 'Callable',
            'content': '',
        }

        self.assertDictEqual(document, expected_result)


class TestElasticSearchDocumentInheritance(TestCase):
    """
    This tests that the ElasticSearchDocument class works well with model inheritance.
    """
    def assertDictEqual(self, a, b):
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def setUp(self):
        # Import using a try-catch block to prevent crashes if the elasticsearch-py
        # module is not installed
        try:
            from wagtail.wagtailsearch.backends.elasticsearch import ElasticSearchDocument
        except ImportError:
            raise unittest.SkipTest("elasticsearch-py not installed")

        # Create ES document
        self.obj = models.SearchTestChild(title="Hello")
        self.obj.save()
        self.es_doc = ElasticSearchDocument(self.obj)

    def test_get_id(self):
        # This must be tests_searchtest instead of 'tests_searchtest_tests_searchtestchild'
        # as it uses the contents base content type name.
        # This prevents the same object being accidentally indexed twice.
        self.assertEqual(self.es_doc.get_id(), 'tests_searchtest:' + str(self.obj.pk))

    def test_build_document(self):
        # Build document
        document = self.es_doc.build_document()

        # Check
        expected_result = {
            # New
            'extra_content': '',
            'searchtest_ptr_id_filter': str(self.obj.pk),

            # Changed
            'content_type': 'tests_searchtest_tests_searchtestchild',

            # Inherited
            'pk': str(self.obj.pk),
            'id': 'tests_searchtest:' + str(self.obj.pk),
            'live_filter': False,
            'published_date_filter': None,
            'title': 'Hello',
            'title_filter': 'Hello',
            'callable_indexed_field': 'Callable',
            'content': '',
        }

        self.assertDictEqual(document, expected_result)
