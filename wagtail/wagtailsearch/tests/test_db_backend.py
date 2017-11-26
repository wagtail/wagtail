import unittest

from django.test import TestCase

from .test_backends import BackendTests


class TestDBBackend(BackendTests, TestCase):
    backend_path = 'wagtail.wagtailsearch.backends.db'

    # Doesn't support ranking
    @unittest.expectedFailure
    def test_ranking(self):
        super(TestDBBackend, self).test_ranking()

    # Doesn't support ranking
    @unittest.expectedFailure
    def test_search_boosting_on_related_fields(self):
        super(TestDBBackend, self).test_search_boosting_on_related_fields()

    # Doesn't support searching specific fields
    @unittest.expectedFailure
    def test_search_child_class_field_from_parent(self):
        super(TestDBBackend, self).test_search_child_class_field_from_parent()

    # Doesn't support searching related fields
    @unittest.expectedFailure
    def test_search_on_related_fields(self):
        super(TestDBBackend, self).test_search_on_related_fields()

    # Doesn't support searching callable fields
    @unittest.expectedFailure
    def test_search_callable_field(self):
        super(TestDBBackend, self).test_search_callable_field()

    # Broken
    @unittest.expectedFailure
    def test_order_by_non_filterable_field(self):
        super(TestDBBackend, self).test_order_by_non_filterable_field()

    # Doesn't support the index API used in this test
    @unittest.expectedFailure
    def test_same_rank_pages(self):
        super(TestDBBackend, self).test_same_rank_pages()
