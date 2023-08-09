import datetime
import json
import unittest
from unittest import mock

from django.db.models import Q
from django.test import TestCase

from wagtail.search.query import MATCH_ALL, Fuzzy, Phrase
from wagtail.test.search import models

from .elasticsearch_common_tests import ElasticsearchCommonSearchBackendTests

try:
    from elasticsearch import VERSION as ELASTICSEARCH_VERSION
    from elasticsearch.serializer import JSONSerializer

    from wagtail.search.backends.elasticsearch5 import Elasticsearch5SearchBackend
except ImportError:
    ELASTICSEARCH_VERSION = (0, 0, 0)


@unittest.skipIf(ELASTICSEARCH_VERSION[0] != 5, "Elasticsearch 5 required")
class TestElasticsearch5SearchBackend(ElasticsearchCommonSearchBackendTests, TestCase):
    backend_path = "wagtail.search.backends.elasticsearch5"


@unittest.skipIf(ELASTICSEARCH_VERSION[0] != 5, "Elasticsearch 5 required")
class TestElasticsearch5SearchQuery(TestCase):
    def assertDictEqual(self, a, b):
        default = JSONSerializer().default
        self.assertEqual(
            json.dumps(a, sort_keys=True, default=default),
            json.dumps(b, sort_keys=True, default=default),
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.query_compiler_class = Elasticsearch5SearchBackend.query_compiler_class
        cls.autocomplete_query_compiler_class = (
            Elasticsearch5SearchBackend.autocomplete_query_compiler_class
        )

    def test_simple(self):
        # Create a query
        query_compiler = self.query_compiler_class(models.Book.objects.all(), "Hello")

        # Check it
        expected_result = {
            "bool": {
                "filter": {"match": {"content_type": "searchtests.Book"}},
                "must": {"match": {"_all": {"query": "Hello"}}},
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_simple_autocomplete(self):
        # Create a query
        query_compiler = self.autocomplete_query_compiler_class(
            models.Book.objects.all(), "Hello"
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": {"match": {"content_type": "searchtests.Book"}},
                "must": {"match": {"_partials": {"query": "Hello"}}},
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_match_all(self):
        # Create a query
        query_compiler = self.query_compiler_class(models.Book.objects.all(), MATCH_ALL)

        # Check it
        expected_result = {
            "bool": {
                "filter": {"match": {"content_type": "searchtests.Book"}},
                "must": {"match_all": {}},
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_and_operator(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.all(), "Hello", operator="and"
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": {"match": {"content_type": "searchtests.Book"}},
                "must": {
                    "match": {
                        "_all": {
                            "query": "Hello",
                            "operator": "and",
                        }
                    }
                },
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_filter(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.filter(title="Test"), "Hello"
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": [
                    {"match": {"content_type": "searchtests.Book"}},
                    {"term": {"title_filter": "Test"}},
                ],
                "must": {"match": {"_all": {"query": "Hello"}}},
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_and_filter(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.filter(
                title="Test", publication_date=datetime.date(2017, 10, 18)
            ),
            "Hello",
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": [
                    {"match": {"content_type": "searchtests.Book"}},
                    {
                        "bool": {
                            "must": [
                                {"term": {"publication_date_filter": "2017-10-18"}},
                                {"term": {"title_filter": "Test"}},
                            ]
                        }
                    },
                ],
                "must": {"match": {"_all": {"query": "Hello"}}},
            }
        }

        # Make sure field filters are sorted (as they can be in any order which may cause false positives)
        query = query_compiler.get_query()
        field_filters = query["bool"]["filter"][1]["bool"]["must"]
        field_filters[:] = sorted(
            field_filters, key=lambda f: list(f["term"].keys())[0]
        )

        self.assertDictEqual(query, expected_result)

    def test_or_filter(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.filter(
                Q(title="Test") | Q(publication_date=datetime.date(2017, 10, 18))
            ),
            "Hello",
        )

        # Make sure field filters are sorted (as they can be in any order which may cause false positives)
        query = query_compiler.get_query()
        field_filters = query["bool"]["filter"][1]["bool"]["should"]
        field_filters[:] = sorted(
            field_filters, key=lambda f: list(f["term"].keys())[0]
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": [
                    {"match": {"content_type": "searchtests.Book"}},
                    {
                        "bool": {
                            "should": [
                                {"term": {"publication_date_filter": "2017-10-18"}},
                                {"term": {"title_filter": "Test"}},
                            ]
                        }
                    },
                ],
                "must": {"match": {"_all": {"query": "Hello"}}},
            }
        }
        self.assertDictEqual(query, expected_result)

    def test_negated_filter(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.exclude(publication_date=datetime.date(2017, 10, 18)),
            "Hello",
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": [
                    {"match": {"content_type": "searchtests.Book"}},
                    {
                        "bool": {
                            "mustNot": {
                                "term": {"publication_date_filter": "2017-10-18"}
                            }
                        }
                    },
                ],
                "must": {"match": {"_all": {"query": "Hello"}}},
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_fields(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.all(), "Hello", fields=["title"]
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": {"match": {"content_type": "searchtests.Book"}},
                "must": {"match": {"title": {"query": "Hello"}}},
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_fields_with_and_operator(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.all(), "Hello", fields=["title"], operator="and"
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": {"match": {"content_type": "searchtests.Book"}},
                "must": {"match": {"title": {"query": "Hello", "operator": "and"}}},
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_multiple_fields(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.all(), "Hello", fields=["title", "content"]
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": {"match": {"content_type": "searchtests.Book"}},
                "must": {
                    "multi_match": {"fields": ["title", "content"], "query": "Hello"}
                },
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_multiple_fields_with_and_operator(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.all(),
            "Hello",
            fields=["title", "content"],
            operator="and",
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": {"match": {"content_type": "searchtests.Book"}},
                "must": {
                    "multi_match": {
                        "fields": ["title", "content"],
                        "query": "Hello",
                        "operator": "and",
                    }
                },
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_exact_lookup(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.filter(title__exact="Test"), "Hello"
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": [
                    {"match": {"content_type": "searchtests.Book"}},
                    {"term": {"title_filter": "Test"}},
                ],
                "must": {"match": {"_all": {"query": "Hello"}}},
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_none_lookup(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.filter(title=None), "Hello"
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": [
                    {"match": {"content_type": "searchtests.Book"}},
                    {"bool": {"mustNot": {"exists": {"field": "title_filter"}}}},
                ],
                "must": {"match": {"_all": {"query": "Hello"}}},
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_isnull_true_lookup(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.filter(title__isnull=True), "Hello"
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": [
                    {"match": {"content_type": "searchtests.Book"}},
                    {"bool": {"mustNot": {"exists": {"field": "title_filter"}}}},
                ],
                "must": {"match": {"_all": {"query": "Hello"}}},
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_isnull_false_lookup(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.filter(title__isnull=False), "Hello"
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": [
                    {"match": {"content_type": "searchtests.Book"}},
                    {"exists": {"field": "title_filter"}},
                ],
                "must": {"match": {"_all": {"query": "Hello"}}},
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_startswith_lookup(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.filter(title__startswith="Test"), "Hello"
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": [
                    {"match": {"content_type": "searchtests.Book"}},
                    {"prefix": {"title_filter": "Test"}},
                ],
                "must": {"match": {"_all": {"query": "Hello"}}},
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_gt_lookup(self):
        # This also tests conversion of python dates to strings

        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.filter(
                publication_date__gt=datetime.datetime(2014, 4, 29)
            ),
            "Hello",
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": [
                    {"match": {"content_type": "searchtests.Book"}},
                    {"range": {"publication_date_filter": {"gt": "2014-04-29"}}},
                ],
                "must": {"match": {"_all": {"query": "Hello"}}},
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_lt_lookup(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.filter(
                publication_date__lt=datetime.datetime(2014, 4, 29)
            ),
            "Hello",
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": [
                    {"match": {"content_type": "searchtests.Book"}},
                    {"range": {"publication_date_filter": {"lt": "2014-04-29"}}},
                ],
                "must": {"match": {"_all": {"query": "Hello"}}},
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_gte_lookup(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.filter(
                publication_date__gte=datetime.datetime(2014, 4, 29)
            ),
            "Hello",
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": [
                    {"match": {"content_type": "searchtests.Book"}},
                    {"range": {"publication_date_filter": {"gte": "2014-04-29"}}},
                ],
                "must": {"match": {"_all": {"query": "Hello"}}},
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_lte_lookup(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.filter(
                publication_date__lte=datetime.datetime(2014, 4, 29)
            ),
            "Hello",
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": [
                    {"match": {"content_type": "searchtests.Book"}},
                    {"range": {"publication_date_filter": {"lte": "2014-04-29"}}},
                ],
                "must": {"match": {"_all": {"query": "Hello"}}},
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_range_lookup(self):
        start_date = datetime.datetime(2014, 4, 29)
        end_date = datetime.datetime(2014, 8, 19)

        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.filter(publication_date__range=(start_date, end_date)),
            "Hello",
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": [
                    {"match": {"content_type": "searchtests.Book"}},
                    {
                        "range": {
                            "publication_date_filter": {
                                "gte": "2014-04-29",
                                "lte": "2014-08-19",
                            }
                        }
                    },
                ],
                "must": {"match": {"_all": {"query": "Hello"}}},
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)

    def test_custom_ordering(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.order_by("publication_date"),
            "Hello",
            order_by_relevance=False,
        )

        # Check it
        expected_result = [{"publication_date_filter": "asc"}]
        self.assertDictEqual(query_compiler.get_sort(), expected_result)

    def test_custom_ordering_reversed(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.order_by("-publication_date"),
            "Hello",
            order_by_relevance=False,
        )

        # Check it
        expected_result = [{"publication_date_filter": "desc"}]
        self.assertDictEqual(query_compiler.get_sort(), expected_result)

    def test_custom_ordering_multiple(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.order_by("publication_date", "number_of_pages"),
            "Hello",
            order_by_relevance=False,
        )

        # Check it
        expected_result = [
            {"publication_date_filter": "asc"},
            {"number_of_pages_filter": "asc"},
        ]
        self.assertDictEqual(query_compiler.get_sort(), expected_result)

    def test_phrase_query(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.all(), Phrase("Hello world")
        )

        # Check it
        expected_result = {
            "match_phrase": {
                "_all": "Hello world",
            }
        }
        self.assertDictEqual(query_compiler.get_inner_query(), expected_result)

    def test_phrase_query_multiple_fields(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.all(),
            Phrase("Hello world"),
            fields=["title", "content"],
        )

        # Check it
        expected_result = {
            "multi_match": {
                "fields": ["title", "content"],
                "query": "Hello world",
                "type": "phrase",
            }
        }
        self.assertDictEqual(query_compiler.get_inner_query(), expected_result)

    def test_phrase_query_single_field(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.all(), Phrase("Hello world"), fields=["title"]
        )

        # Check it
        expected_result = {"match_phrase": {"title": "Hello world"}}
        self.assertDictEqual(query_compiler.get_inner_query(), expected_result)

    def test_fuzzy_query(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.all(),
            Fuzzy("Hello world"),
        )

        # Check it
        expected_result = {
            "match": {"_all": {"query": "Hello world", "fuzziness": "AUTO"}}
        }
        self.assertDictEqual(query_compiler.get_inner_query(), expected_result)

    def test_fuzzy_query_single_field(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.all(),
            Fuzzy("Hello world"),
            fields=["title"],
        )

        # Check it
        expected_result = {
            "match": {"title": {"query": "Hello world", "fuzziness": "AUTO"}}
        }
        self.assertDictEqual(query_compiler.get_inner_query(), expected_result)

    def test_fuzzy_query_multiple_fields_disallowed(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.all(),
            Fuzzy("Hello world"),
            fields=["title", "body"],
        )

        # Check it
        with self.assertRaises(NotImplementedError):
            query_compiler.get_inner_query()

    def test_year_filter(self):
        # Create a query
        query_compiler = self.query_compiler_class(
            models.Book.objects.filter(publication_date__year__gt=1900), "Hello"
        )

        # Check it
        expected_result = {
            "bool": {
                "filter": [
                    {"match": {"content_type": "searchtests.Book"}},
                    {"range": {"publication_date_filter": {"gte": "1901-01-01"}}},
                ],
                "must": {"match": {"_all": {"query": "Hello"}}},
            }
        }
        self.assertDictEqual(query_compiler.get_query(), expected_result)


@unittest.skipIf(ELASTICSEARCH_VERSION[0] != 5, "Elasticsearch 5 required")
class TestElasticsearch5SearchResults(TestCase):
    fixtures = ["search"]

    def assertDictEqual(self, a, b):
        default = JSONSerializer().default
        self.assertEqual(json.dumps(a, sort_keys=True, default=default), json.dumps)

    def get_results(self):
        backend = Elasticsearch5SearchBackend({})
        query_compiler = mock.MagicMock()
        query_compiler.queryset = models.Book.objects.all()
        query_compiler.get_query.return_value = "QUERY"
        query_compiler.get_sort.return_value = None
        return backend.results_class(backend, query_compiler)

    def construct_search_response(self, results):
        return {
            "_shards": {"failed": 0, "successful": 5, "total": 5},
            "hits": {
                "hits": [
                    {
                        "_id": "searchtests_book:" + str(result),
                        "_index": "wagtail",
                        "_score": 1,
                        "_type": "searchtests_book",
                        "fields": {
                            "pk": [str(result)],
                        },
                    }
                    for result in results
                ],
                "max_score": 1,
                "total": len(results),
            },
            "timed_out": False,
            "took": 2,
        }

    @mock.patch("elasticsearch.Elasticsearch.search")
    def test_basic_search(self, search):
        search.return_value = self.construct_search_response([])
        results = self.get_results()

        list(results)  # Performs search

        search.assert_any_call(
            body={"query": "QUERY"},
            _source=False,
            stored_fields="pk",
            index="wagtail__searchtests_book",
            scroll="2m",
            size=100,
        )

    @mock.patch("elasticsearch.Elasticsearch.search")
    def test_get_single_item(self, search):
        # Need to return something to prevent index error
        search.return_value = self.construct_search_response([1])
        results = self.get_results()

        results[10]  # Performs search

        search.assert_any_call(
            from_=10,
            body={"query": "QUERY"},
            _source=False,
            stored_fields="pk",
            index="wagtail__searchtests_book",
            size=1,
        )

    @mock.patch("elasticsearch.Elasticsearch.search")
    def test_slice_results(self, search):
        search.return_value = self.construct_search_response([])
        results = self.get_results()[1:4]

        list(results)  # Performs search

        search.assert_any_call(
            from_=1,
            body={"query": "QUERY"},
            _source=False,
            stored_fields="pk",
            index="wagtail__searchtests_book",
            size=3,
        )

    @mock.patch("elasticsearch.Elasticsearch.search")
    def test_slice_results_multiple_times(self, search):
        search.return_value = self.construct_search_response([])
        results = self.get_results()[10:][:10]

        list(results)  # Performs search

        search.assert_any_call(
            from_=10,
            body={"query": "QUERY"},
            _source=False,
            stored_fields="pk",
            index="wagtail__searchtests_book",
            size=10,
        )

    @mock.patch("elasticsearch.Elasticsearch.search")
    def test_slice_results_and_get_item(self, search):
        # Need to return something to prevent index error
        search.return_value = self.construct_search_response([1])
        results = self.get_results()[10:]

        results[10]  # Performs search

        search.assert_any_call(
            from_=20,
            body={"query": "QUERY"},
            _source=False,
            stored_fields="pk",
            index="wagtail__searchtests_book",
            size=1,
        )

    @mock.patch("elasticsearch.Elasticsearch.search")
    def test_result_returned(self, search):
        search.return_value = self.construct_search_response([1])
        results = self.get_results()

        self.assertEqual(results[0], models.Book.objects.get(id=1))

    @mock.patch("elasticsearch.Elasticsearch.search")
    def test_len_1(self, search):
        search.return_value = self.construct_search_response([1])
        results = self.get_results()

        self.assertEqual(len(results), 1)

    @mock.patch("elasticsearch.Elasticsearch.search")
    def test_len_2(self, search):
        search.return_value = self.construct_search_response([1, 2])
        results = self.get_results()

        self.assertEqual(len(results), 2)

    @mock.patch("elasticsearch.Elasticsearch.search")
    def test_duplicate_results(self, search):  # Duplicates will not be removed
        search.return_value = self.construct_search_response([1, 1])
        results = list(
            self.get_results()
        )  # Must cast to list so we only create one query

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], models.Book.objects.get(id=1))
        self.assertEqual(results[1], models.Book.objects.get(id=1))

    @mock.patch("elasticsearch.Elasticsearch.search")
    def test_result_order(self, search):
        search.return_value = self.construct_search_response([1, 2, 3])
        results = list(
            self.get_results()
        )  # Must cast to list so we only create one query

        self.assertEqual(results[0], models.Book.objects.get(id=1))
        self.assertEqual(results[1], models.Book.objects.get(id=2))
        self.assertEqual(results[2], models.Book.objects.get(id=3))

    @mock.patch("elasticsearch.Elasticsearch.search")
    def test_result_order_2(self, search):
        search.return_value = self.construct_search_response([3, 2, 1])
        results = list(
            self.get_results()
        )  # Must cast to list so we only create one query

        self.assertEqual(results[0], models.Book.objects.get(id=3))
        self.assertEqual(results[1], models.Book.objects.get(id=2))
        self.assertEqual(results[2], models.Book.objects.get(id=1))


@unittest.skipIf(ELASTICSEARCH_VERSION[0] != 5, "Elasticsearch 5 required")
class TestElasticsearch5Mapping(TestCase):
    fixtures = ["search"]

    def assertDictEqual(self, a, b):
        default = JSONSerializer().default
        self.assertEqual(
            json.dumps(a, sort_keys=True, default=default),
            json.dumps(b, sort_keys=True, default=default),
        )

    def setUp(self):
        # Create ES mapping
        self.es_mapping = Elasticsearch5SearchBackend.mapping_class(models.Book)

        # Create ES document
        self.obj = models.Book.objects.get(id=4)

    def test_get_document_type(self):
        self.assertEqual(self.es_mapping.get_document_type(), "searchtests_book")

    def test_get_mapping(self):
        # Build mapping
        mapping = self.es_mapping.get_mapping()

        # Check
        expected_result = {
            "searchtests_book": {
                "properties": {
                    "pk": {"type": "keyword", "store": True, "include_in_all": False},
                    "content_type": {"type": "keyword", "include_in_all": False},
                    "_partials": {
                        "analyzer": "edgengram_analyzer",
                        "search_analyzer": "standard",
                        "include_in_all": False,
                        "type": "text",
                    },
                    "title": {
                        "type": "text",
                        "boost": 2.0,
                        "include_in_all": True,
                    },
                    "title_edgengrams": {
                        "type": "text",
                        "include_in_all": False,
                        "analyzer": "edgengram_analyzer",
                        "search_analyzer": "standard",
                    },
                    "title_filter": {"type": "keyword", "include_in_all": False},
                    "authors": {
                        "type": "nested",
                        "properties": {
                            "name": {"type": "text", "include_in_all": True},
                            "name_edgengrams": {
                                "analyzer": "edgengram_analyzer",
                                "include_in_all": False,
                                "search_analyzer": "standard",
                                "type": "text",
                            },
                            "date_of_birth_filter": {
                                "type": "date",
                                "include_in_all": False,
                            },
                        },
                    },
                    "authors_filter": {"type": "integer", "include_in_all": False},
                    "publication_date_filter": {
                        "type": "date",
                        "include_in_all": False,
                    },
                    "number_of_pages_filter": {
                        "type": "integer",
                        "include_in_all": False,
                    },
                    "tags": {
                        "type": "nested",
                        "properties": {
                            "name": {"type": "text", "include_in_all": True},
                            "slug_filter": {"type": "keyword", "include_in_all": False},
                        },
                    },
                    "tags_filter": {"type": "integer", "include_in_all": False},
                }
            }
        }

        self.assertDictEqual(mapping, expected_result)

    def test_get_document_id(self):
        self.assertEqual(
            self.es_mapping.get_document_id(self.obj),
            "searchtests_book:" + str(self.obj.pk),
        )

    def test_get_document(self):
        # Get document
        document = self.es_mapping.get_document(self.obj)

        # Sort partials
        if "_partials" in document:
            document["_partials"].sort()

        # Check
        expected_result = {
            "pk": "4",
            "content_type": ["searchtests.Book"],
            "_partials": [
                "J. R. R. Tolkien",
                "The Fellowship of the Ring",
            ],
            "title": "The Fellowship of the Ring",
            "title_edgengrams": "The Fellowship of the Ring",
            "title_filter": "The Fellowship of the Ring",
            "authors": [
                {
                    "name": "J. R. R. Tolkien",
                    "name_edgengrams": "J. R. R. Tolkien",
                    "date_of_birth_filter": datetime.date(1892, 1, 3),
                }
            ],
            "authors_filter": [2],
            "publication_date_filter": datetime.date(1954, 7, 29),
            "number_of_pages_filter": 423,
            "tags": [],
            "tags_filter": [],
        }

        self.assertDictEqual(document, expected_result)


@unittest.skipIf(ELASTICSEARCH_VERSION[0] != 5, "Elasticsearch 5 required")
class TestElasticsearch5MappingInheritance(TestCase):
    fixtures = ["search"]

    def assertDictEqual(self, a, b):
        default = JSONSerializer().default
        self.assertEqual(
            json.dumps(a, sort_keys=True, default=default),
            json.dumps(b, sort_keys=True, default=default),
        )

    def setUp(self):
        # Create ES mapping
        self.es_mapping = Elasticsearch5SearchBackend.mapping_class(models.Novel)

        self.obj = models.Novel.objects.get(id=4)

    def test_get_document_type(self):
        self.assertEqual(
            self.es_mapping.get_document_type(), "searchtests_book_searchtests_novel"
        )

    def test_get_mapping(self):
        # Build mapping
        mapping = self.es_mapping.get_mapping()

        # Check
        expected_result = {
            "searchtests_book_searchtests_novel": {
                "properties": {
                    # New
                    "searchtests_novel__setting": {
                        "type": "text",
                        "include_in_all": True,
                    },
                    "searchtests_novel__setting_edgengrams": {
                        "type": "text",
                        "include_in_all": False,
                        "analyzer": "edgengram_analyzer",
                        "search_analyzer": "standard",
                    },
                    "searchtests_novel__protagonist": {
                        "type": "nested",
                        "properties": {
                            "name": {
                                "type": "text",
                                "boost": 0.5,
                                "include_in_all": True,
                            },
                            "novel_id_filter": {
                                "type": "integer",
                                "include_in_all": False,
                            },
                        },
                    },
                    "searchtests_novel__protagonist_id_filter": {
                        "type": "integer",
                        "include_in_all": False,
                    },
                    "searchtests_novel__characters": {
                        "type": "nested",
                        "properties": {
                            "name": {
                                "type": "text",
                                "boost": 0.25,
                                "include_in_all": True,
                            }
                        },
                    },
                    # Inherited
                    "pk": {"type": "keyword", "store": True, "include_in_all": False},
                    "content_type": {"type": "keyword", "include_in_all": False},
                    "_partials": {
                        "analyzer": "edgengram_analyzer",
                        "search_analyzer": "standard",
                        "include_in_all": False,
                        "type": "text",
                    },
                    "title": {
                        "type": "text",
                        "boost": 2.0,
                        "include_in_all": True,
                    },
                    "title_edgengrams": {
                        "type": "text",
                        "include_in_all": False,
                        "analyzer": "edgengram_analyzer",
                        "search_analyzer": "standard",
                    },
                    "title_filter": {"type": "keyword", "include_in_all": False},
                    "authors": {
                        "type": "nested",
                        "properties": {
                            "name": {"type": "text", "include_in_all": True},
                            "name_edgengrams": {
                                "analyzer": "edgengram_analyzer",
                                "include_in_all": False,
                                "search_analyzer": "standard",
                                "type": "text",
                            },
                            "date_of_birth_filter": {
                                "type": "date",
                                "include_in_all": False,
                            },
                        },
                    },
                    "authors_filter": {"type": "integer", "include_in_all": False},
                    "publication_date_filter": {
                        "type": "date",
                        "include_in_all": False,
                    },
                    "number_of_pages_filter": {
                        "type": "integer",
                        "include_in_all": False,
                    },
                    "tags": {
                        "type": "nested",
                        "properties": {
                            "name": {"type": "text", "include_in_all": True},
                            "slug_filter": {"type": "keyword", "include_in_all": False},
                        },
                    },
                    "tags_filter": {"type": "integer", "include_in_all": False},
                }
            }
        }

        self.assertDictEqual(mapping, expected_result)

    def test_get_document_id(self):
        # This must be tests_searchtest instead of 'tests_searchtest_tests_searchtestchild'
        # as it uses the contents base content type name.
        # This prevents the same object being accidentally indexed twice.
        self.assertEqual(
            self.es_mapping.get_document_id(self.obj),
            "searchtests_book:" + str(self.obj.pk),
        )

    def test_get_document(self):
        # Build document
        document = self.es_mapping.get_document(self.obj)

        # Sort partials
        if "_partials" in document:
            document["_partials"].sort()

        # Sort characters
        if "searchtests_novel__characters" in document:
            document["searchtests_novel__characters"].sort(key=lambda c: c["name"])

        # Check
        expected_result = {
            # New
            "searchtests_novel__setting": "Middle Earth",
            "searchtests_novel__setting_edgengrams": "Middle Earth",
            "searchtests_novel__protagonist": {
                "name": "Frodo Baggins",
                "novel_id_filter": 4,
            },
            "searchtests_novel__protagonist_id_filter": 8,
            "searchtests_novel__characters": [
                {"name": "Bilbo Baggins"},
                {"name": "Frodo Baggins"},
                {"name": "Gandalf"},
            ],
            # Changed
            "content_type": ["searchtests.Novel", "searchtests.Book"],
            "_partials": [
                "J. R. R. Tolkien",
                "Middle Earth",
                "The Fellowship of the Ring",
            ],
            # Inherited
            "pk": "4",
            "title": "The Fellowship of the Ring",
            "title_edgengrams": "The Fellowship of the Ring",
            "title_filter": "The Fellowship of the Ring",
            "authors": [
                {
                    "name": "J. R. R. Tolkien",
                    "name_edgengrams": "J. R. R. Tolkien",
                    "date_of_birth_filter": datetime.date(1892, 1, 3),
                }
            ],
            "authors_filter": [2],
            "publication_date_filter": datetime.date(1954, 7, 29),
            "number_of_pages_filter": 423,
            "tags": [],
            "tags_filter": [],
        }

        self.assertDictEqual(document, expected_result)


@unittest.skipIf(ELASTICSEARCH_VERSION[0] != 5, "Elasticsearch 5 required")
@mock.patch("wagtail.search.backends.elasticsearch5.Elasticsearch")
class TestBackendConfiguration(TestCase):
    def test_default_settings(self, Elasticsearch):
        Elasticsearch5SearchBackend(params={})

        Elasticsearch.assert_called_with(
            hosts=[
                {
                    "host": "localhost",
                    "port": 9200,
                    "url_prefix": "",
                    "use_ssl": False,
                    "verify_certs": False,
                    "http_auth": None,
                }
            ],
            timeout=10,
        )

    def test_hosts(self, Elasticsearch):
        Elasticsearch5SearchBackend(
            params={
                "HOSTS": [
                    {
                        "host": "127.0.0.1",
                        "port": 9300,
                        "use_ssl": True,
                        "verify_certs": True,
                    }
                ]
            }
        )

        Elasticsearch.assert_called_with(
            hosts=[
                {
                    "host": "127.0.0.1",
                    "port": 9300,
                    "use_ssl": True,
                    "verify_certs": True,
                }
            ],
            timeout=10,
        )

    def test_urls(self, Elasticsearch):
        # This test backwards compatibility with old URLS setting
        Elasticsearch5SearchBackend(
            params={
                "URLS": [
                    "http://localhost:12345",
                    "https://127.0.0.1:54321",
                    "http://username:password@elasticsearch.mysite.com",
                    "https://elasticsearch.mysite.com/hello",
                ],
            }
        )

        Elasticsearch.assert_called_with(
            hosts=[
                {
                    "host": "localhost",
                    "port": 12345,
                    "url_prefix": "",
                    "use_ssl": False,
                    "verify_certs": False,
                    "http_auth": None,
                },
                {
                    "host": "127.0.0.1",
                    "port": 54321,
                    "url_prefix": "",
                    "use_ssl": True,
                    "verify_certs": True,
                    "http_auth": None,
                },
                {
                    "host": "elasticsearch.mysite.com",
                    "port": 80,
                    "url_prefix": "",
                    "use_ssl": False,
                    "verify_certs": False,
                    "http_auth": ("username", "password"),
                },
                {
                    "host": "elasticsearch.mysite.com",
                    "port": 443,
                    "url_prefix": "/hello",
                    "use_ssl": True,
                    "verify_certs": True,
                    "http_auth": None,
                },
            ],
            timeout=10,
        )
