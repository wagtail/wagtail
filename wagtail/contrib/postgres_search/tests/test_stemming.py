from django.test import TestCase

from wagtail.search.backends import get_search_backend
from wagtail.tests.search import models


class TestPostgresStemming(TestCase):
    def setUp(self):
        self.backend = get_search_backend(
            'wagtail.contrib.postgres_search.backend'
        )
        self.ru_book = models.Book.objects.create(
            title="Голубое сало", publication_date="1999-05-01",
            number_of_pages=352
        )
        self.backend.add(self.ru_book)

    def test_ru_stemming(self):
        results = self.backend.search("Голубое", models.Book)
        self.assertEqual(list(results), [self.ru_book])

        results = self.backend.search("Голубая", models.Book)
        self.assertEqual(list(results), [self.ru_book])

        results = self.backend.search("Голубой", models.Book)
        self.assertEqual(list(results), [self.ru_book])
