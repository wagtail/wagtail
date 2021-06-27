import unittest

from django.conf import settings
from django.db import connection
from django.test import TestCase

from wagtail.search.backends import get_search_backend
from wagtail.tests.search import models


class TestPostgresStemming(TestCase):
    def setUp(self):
        backend_name = "wagtail.search.backends.database.postgres"
        for conf in settings.WAGTAILSEARCH_BACKENDS.values():
            if conf['BACKEND'] == backend_name:
                break
        else:
            raise unittest.SkipTest("Only for %s" % backend_name)

        self.backend = get_search_backend(backend_name)

    def test_ru_stemming(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "SET default_text_search_config TO 'pg_catalog.russian'"
            )

        ru_book = models.Book.objects.create(
            title="Голубое сало", publication_date="1999-05-01",
            number_of_pages=352
        )
        self.backend.add(ru_book)

        results = self.backend.search("Голубое", models.Book)
        self.assertEqual(list(results), [ru_book])

        results = self.backend.search("Голубая", models.Book)
        self.assertEqual(list(results), [ru_book])

        results = self.backend.search("Голубой", models.Book)
        self.assertEqual(list(results), [ru_book])

        ru_book.delete()
