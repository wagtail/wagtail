import unittest

from django.db import connection
from django.test import TestCase
from django.test.utils import override_settings

from wagtail.search.query import MatchAll, Phrase
from wagtail.search.tests.test_backends import BackendTests
from wagtail.test.search import models


@unittest.skipUnless(
    connection.vendor == "postgresql", "The current database is not PostgreSQL"
)
@override_settings(
    WAGTAILSEARCH_BACKENDS={
        "default": {
            "BACKEND": "wagtail.search.backends.database.postgres.postgres",
        }
    }
)
class TestPostgresSearchBackend(BackendTests, TestCase):
    backend_path = "wagtail.search.backends.database.postgres.postgres"

    def test_weights(self):
        from ..backends.database.postgres.weights import (
            BOOSTS_WEIGHTS,
            WEIGHTS_VALUES,
            determine_boosts_weights,
            get_weight,
        )

        self.assertListEqual(
            BOOSTS_WEIGHTS, [(10, "A"), (2, "B"), (0.5, "C"), (0.25, "D")]
        )
        self.assertListEqual(WEIGHTS_VALUES, [0.025, 0.05, 0.2, 1.0])

        self.assertEqual(get_weight(15), "A")
        self.assertEqual(get_weight(10), "A")
        self.assertEqual(get_weight(9.9), "B")
        self.assertEqual(get_weight(2), "B")
        self.assertEqual(get_weight(1.9), "C")
        self.assertEqual(get_weight(0), "D")
        self.assertEqual(get_weight(-1), "D")

        self.assertListEqual(
            determine_boosts_weights([1]), [(1, "A"), (0, "B"), (0, "C"), (0, "D")]
        )
        self.assertListEqual(
            determine_boosts_weights([-1]), [(-1, "A"), (-1, "B"), (-1, "C"), (-1, "D")]
        )
        self.assertListEqual(
            determine_boosts_weights([-1, 1, 2]),
            [(2, "A"), (1, "B"), (-1, "C"), (-1, "D")],
        )
        self.assertListEqual(
            determine_boosts_weights([0, 1, 2, 3]),
            [(3, "A"), (2, "B"), (1, "C"), (0, "D")],
        )
        self.assertListEqual(
            determine_boosts_weights([0, 0.25, 0.75, 1, 1.5]),
            [(1.5, "A"), (1, "B"), (0.5, "C"), (0, "D")],
        )
        self.assertListEqual(
            determine_boosts_weights([0, 1, 2, 3, 4, 5, 6]),
            [(6, "A"), (4, "B"), (2, "C"), (0, "D")],
        )
        self.assertListEqual(
            determine_boosts_weights([-2, -1, 0, 1, 2, 3, 4]),
            [(4, "A"), (2, "B"), (0, "C"), (-2, "D")],
        )

    def test_search_tsquery_chars(self):
        """
        Checks that tsquery characters are correctly escaped
        and do not generate a PostgreSQL syntax error.
        """

        # Simple quote should be escaped inside each tsquery term.
        results = self.backend.search("L'amour piqué par une abeille", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])
        results = self.backend.search("'starting quote", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])
        results = self.backend.search("ending quote'", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])
        results = self.backend.search("double quo''te", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])
        results = self.backend.search("triple quo'''te", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])

        # Now suffixes.
        results = self.backend.search("Something:B", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])
        results = self.backend.search("Something:*", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])
        results = self.backend.search("Something:A*BCD", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])

        # Now the AND operator.
        results = self.backend.search("first & second", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])

        # Now the OR operator.
        results = self.backend.search("first | second", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])

        # Now the NOT operator.
        results = self.backend.search("first & !second", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])

        # Now the phrase operator.
        results = self.backend.search("first <-> second", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])

    def test_autocomplete_tsquery_chars(self):
        """
        Checks that tsquery characters are correctly escaped
        and do not generate a PostgreSQL syntax error.
        """

 
        results = self.backend.autocomplete(
            "L'amour piqué par une abeille", models.Book
        )
        self.assertUnsortedListEqual([r.title for r in results], [])
        results = self.backend.autocomplete("'starting quote", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])
        results = self.backend.autocomplete("ending quote'", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])
        results = self.backend.autocomplete("double quo''te", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])
        results = self.backend.autocomplete("triple quo'''te", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])


        results = self.backend.autocomplete("backslash\\", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])

        # Now suffixes.
        results = self.backend.autocomplete("Something:B", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])
        results = self.backend.autocomplete("Something:*", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])
        results = self.backend.autocomplete("Something:A*BCD", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])

        # Now the AND operator.
        results = self.backend.autocomplete("first & second", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])

        # Now the OR operator.
        results = self.backend.autocomplete("first | second", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])

        # Now the NOT operator.
        results = self.backend.autocomplete("first & !second", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])

        # Now the phrase operator.
        results = self.backend.autocomplete("first <-> second", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [])


@unittest.skipUnless(
    connection.vendor == "postgresql", "The current database is not PostgreSQL"
)
@override_settings(
    WAGTAILSEARCH_BACKENDS={
        "default": {
            "BACKEND": "wagtail.search.backends.database.postgres.postgres",
            "SEARCH_CONFIG": "dutch",
        }
    }
)
class TestPostgresLanguageTextSearch(TestCase):
    backend_path = "wagtail.search.backends.database.postgres.postgres"

    def setUp(self):
   
        BackendTests.setUp(self)

        book = models.Book.objects.create(
            title="Nu is beter dan nooit",
            publication_date="1999-05-01",
            number_of_pages=333,
        )
        self.backend.add(book)
        self.book = book

    def test_search_language_plain_text(self):
        results = self.backend.search("Nu is beter dan nooit", models.Book)
        self.assertEqual(list(results), [self.book])

        results = self.backend.search("is beter", models.Book)
        self.assertEqual(list(results), [self.book])


        results = self.backend.search("zijn beter", models.Book)
        self.assertEqual(list(results), [self.book])

        results = self.backend.search("zij beter dan", models.Book)
        self.assertEqual(list(results), [self.book])

    def test_search_language_phrase_text(self):
        results = self.backend.search(Phrase("Nu is beter"), models.Book)
        self.assertEqual(list(results), [self.book])

        results = self.backend.search(Phrase("Nu zijn beter"), models.Book)
        self.assertEqual(list(results), [self.book])


@unittest.skipUnless(
    connection.vendor == "postgresql", "The current database is not PostgreSQL"
)
@override_settings(
    WAGTAILSEARCH_BACKENDS={
        "default": {
            "BACKEND": "wagtail.search.backends.database.postgres.postgres",
        }
    }
)
class TestPostgresSearchBackendUnequalLists(TestCase):
    """
    Test that the PostgreSQL backend can handle objects with empty searchable fields.

    These tests verify the fix for issue #12996, where indexing objects with empty
    searchable fields would cause an IndexError when the lists of search values
    had different lengths.
    """

    def setUp(self):
        # Create a book with only title (empty summary)
        self.book_with_title_only = models.Book.objects.create(
            title="Book with title only",
            summary="",
            publication_date="2025-01-01",
            number_of_pages=100,
        )

        # Create a book with multiple empty fields
        self.minimal_book = models.Book.objects.create(
            title=" ", summary="", publication_date="2025-01-01", number_of_pages=0
        )

        # Create a book with all fields populated
        self.complete_book = models.Book.objects.create(
            title="Complete Book",
            summary="This book has all fields populated",
            publication_date="2025-01-01",
            number_of_pages=200,
        )

        from wagtail.search.backends import get_search_backend

        self.backend = get_search_backend()

        self.assertEqual(
            self.backend.__class__.__module__,
            "wagtail.search.backends.database.postgres.postgres",
        )

    def test_indexing_with_empty_fields(self):
        """Test indexing objects with empty fields doesn't cause an IndexError."""
   
        self.backend.add(self.minimal_book)


        all_results = self.backend.search(MatchAll(), models.Book)
        self.assertIn(self.minimal_book.id, [r.id for r in all_results])

    def test_indexing_mixed_empty_fields(self):
        """Test indexing a mix of objects with empty and populated fields."""
       
        self.backend.add_bulk(
            models.Book,
            [self.minimal_book, self.book_with_title_only, self.complete_book],
        )

      
        all_results = list(self.backend.search("book", models.Book))
        self.assertEqual(
            len(all_results), 2
        ) 

        summary_results = list(self.backend.search("fields populated", models.Book))
        self.assertEqual(len(summary_results), 1)
        self.assertEqual(summary_results[0].id, self.complete_book.id)

    def test_varying_field_content(self):
        """Test indexing and searching objects with content in different fields."""
    
        fantasy_book = models.Book.objects.create(
            title="Fantasy Adventure",
            summary="", 
            publication_date="2025-01-01",
            number_of_pages=300,
        )

        sci_fi_book = models.Book.objects.create(
            title="", 
            summary="Science fiction story about space travel",
            publication_date="2025-01-01",
            number_of_pages=250,
        )

      
        self.backend.add_bulk(models.Book, [fantasy_book, sci_fi_book])

       
        title_results = list(self.backend.search("Fantasy", models.Book))
        self.assertEqual(len(title_results), 1)
        self.assertEqual(title_results[0].id, fantasy_book.id)

      
        summary_results = list(self.backend.search("science fiction", models.Book))
        self.assertEqual(len(summary_results), 1)
        self.assertEqual(summary_results[0].id, sci_fi_book.id)

      
        all_results = list(self.backend.search(MatchAll(), models.Book))
        result_ids = [r.id for r in all_results]
        self.assertIn(fantasy_book.id, result_ids)
        self.assertIn(sci_fi_book.id, result_ids)
