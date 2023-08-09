import unittest

from django.test import TestCase

from .elasticsearch_common_tests import ElasticsearchCommonSearchBackendTests

try:
    from elasticsearch import VERSION as ELASTICSEARCH_VERSION
except ImportError:
    ELASTICSEARCH_VERSION = (0, 0, 0)


@unittest.skipIf(ELASTICSEARCH_VERSION[0] != 8, "Elasticsearch 8 required")
class TestElasticsearch8SearchBackend(ElasticsearchCommonSearchBackendTests, TestCase):
    backend_path = "wagtail.search.backends.elasticsearch8"
