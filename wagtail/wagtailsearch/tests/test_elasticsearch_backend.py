from wagtail.tests.utils import unittest

from django.test import TestCase

from .test_backends import BackendTests


class TestElasticSearchBackend(BackendTests, TestCase):
    backend_path = 'wagtail.wagtailsearch.backends.elasticsearch.ElasticSearch'

    def test_search_with_spaces_only(self):
        # Search for some space characters and hope it doesn't crash
        results = self.backend.search("   ", models.SearchTest)

        # Queries are lazily evaluated, force it to run
        list(results)

        # Didn't crash, yay!
