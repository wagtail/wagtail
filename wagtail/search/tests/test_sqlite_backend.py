import sqlite3
import unittest
from unittest import skip

from django.db import connection
from django.test.testcases import TestCase
from django.test.utils import override_settings

from wagtail.search.backends.database.sqlite.utils import fts5_available
from wagtail.search.tests.test_backends import BackendTests


@unittest.skipUnless(
    connection.vendor == "sqlite", "The current database is not SQLite"
)
@unittest.skipIf(
    sqlite3.sqlite_version_info < (3, 19, 0), "This SQLite version is not supported"
)
@unittest.skipUnless(fts5_available(), "The SQLite fts5 extension is not available")
@override_settings(
    WAGTAILSEARCH_BACKENDS={
        "default": {
            "BACKEND": "wagtail.search.backends.database.sqlite.sqlite",
        }
    }
)
class TestSQLiteSearchBackend(BackendTests, TestCase):
    backend_path = "wagtail.search.backends.database.sqlite.sqlite"

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

    @skip("The SQLite backend doesn't support searching on specified fields.")
    def test_autocomplete_with_fields_arg(self):
        return super().test_autocomplete_with_fields_arg()

    @skip("The SQLite backend doesn't guarantee correct ranking of results.")
    def test_ranking(self):
        return super().test_ranking()
