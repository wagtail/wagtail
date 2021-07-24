from unittest import skip
from wagtail.tests.search import models
from django.test.testcases import TestCase
from wagtail.search.tests.test_backends import BackendTests


class TestSQLiteSearchBackend(BackendTests, TestCase):
    backend_path = 'wagtail.search.backends.database.sqlite'

    @skip("The SQLite backend doesn't support boosting.")
    def test_search_boosting_on_related_fields(self):
        return super().test_search_boosting_on_related_fields()

    @skip("The SQLite backend doesn't support boosting.")
    def test_boost(self):
        return super().test_boost()

    @skip("The SQLite backend doesn't score annotations.")
    def test_annotate_score(self):
        return super().test_annotate_score()

    @skip("The SQLite backend doesn't score annotations.")
    def test_annotate_score_with_slice(self):
        return super().test_annotate_score_with_slice()

    @skip("The SQLite backend doesn't support autocomplete.")
    def test_autocomplete(self):
        return super().test_autocomplete()

    @skip("The SQLite backend doesn't support autocomplete.")
    def test_autocomplete_not_affected_by_stemming(self):
        return super().test_autocomplete_not_affected_by_stemming()

    @skip("The SQLite backend doesn't support autocomplete.")
    def test_autocomplete_uses_autocompletefield(self):
        return super().test_autocomplete_uses_autocompletefield()

    @skip("The SQLite backend doesn't support autocomplete.")
    def test_autocomplete_with_fields_arg(self):
        return super().test_autocomplete_with_fields_arg()

    @skip("The SQLite backend doesn't guarantee correct ranking of results.")
    def test_ranking(self):
        return super().test_ranking()
