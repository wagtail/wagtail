import unittest

from django.test import TestCase

from .test_backends import BackendTests


class TestDBBackend(BackendTests, TestCase):
    backend_path = 'wagtail.search.backends.db'

    # Doesn't support autocomplete
    @unittest.expectedFailure
    def test_autocomplete(self):
        super().test_autocomplete()

    # Doesn't support ranking
    @unittest.expectedFailure
    def test_ranking(self):
        super().test_ranking()

    # Doesn't support ranking
    @unittest.expectedFailure
    def test_annotate_score(self):
        super().test_annotate_score()

    # Doesn't support ranking
    @unittest.expectedFailure
    def test_annotate_score_with_slice(self):
        super().test_annotate_score_with_slice()

    # Doesn't support ranking
    @unittest.expectedFailure
    def test_search_boosting_on_related_fields(self):
        super().test_search_boosting_on_related_fields()

    # Doesn't support searching specific fields
    @unittest.expectedFailure
    def test_search_child_class_field_from_parent(self):
        super().test_search_child_class_field_from_parent()

    # Doesn't support searching related fields
    @unittest.expectedFailure
    def test_search_on_related_fields(self):
        super().test_search_on_related_fields()

    # Doesn't support searching callable fields
    @unittest.expectedFailure
    def test_search_callable_field(self):
        super().test_search_callable_field()

    # Database backend always uses `icontains`, so always autocomplete
    @unittest.expectedFailure
    def test_incomplete_term(self):
        super().test_incomplete_term()

    # Database backend always uses `icontains`, so always autocomplete
    @unittest.expectedFailure
    def test_incomplete_plain_text(self):
        super().test_incomplete_plain_text()

    # Database backend doesn't support Boost() query class
    @unittest.expectedFailure
    def test_boost(self):
        super().test_boost()
