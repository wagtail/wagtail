from django.test import TestCase

from .elasticsearch_common_tests import ElasticsearchCommonSearchBackendTests


class TestElasticsearch8SearchBackend(ElasticsearchCommonSearchBackendTests, TestCase):
    backend_path = "wagtail.search.backends.elasticsearch8"
