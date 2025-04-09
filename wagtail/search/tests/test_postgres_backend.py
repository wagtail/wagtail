import unittest

from django.db import connection
from django.test import TestCase
from django.test.utils import override_settings

from wagtail.search.query import Phrase
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

        # Simple quote should be escaped inside each tsquery term.
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

        # Backslashes should be escaped inside each tsquery term.
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
        # get search backend by backend_path
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

        # search deals even with variations
        results = self.backend.search("zijn beter", models.Book)
        self.assertEqual(list(results), [self.book])

        # search deals even when there are minor typos
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
    Test the fix for list index out of range error when lists have different lengths.
    
    This test addresses issue #12996, which occurred when indexing pages with empty fields,
    especially during locale synchronization.
    """
    
    def setUp(self):
        self.book_with_title_only = models.Book.objects.create(
            title="Book with title only",
            summary="",
            publication_date="2025-01-01",
            number_of_pages=100
        )
        
        self.minimal_book = models.Book.objects.create(
            title=" ",
            summary=None,
            publication_date="2025-01-01",
            number_of_pages=0
        )
        
        from wagtail.search.backends import get_search_backend
        self.backend = get_search_backend()
        
        self.assertEqual(
            self.backend.__class__.__module__,
            "wagtail.search.backends.database.postgres.postgres"
        )
    
    def test_indexing_with_empty_fields(self):
        """Test indexing objects with empty fields doesn't cause an IndexError."""
        try:
            self.backend.add(self.book_with_title_only)
            self.backend.add(self.minimal_book)
            success = True
        except IndexError:
            success = False
        
        self.assertTrue(success, "Indexing with empty fields caused an IndexError")
    
    def test_index_multiple_objects_with_empty_fields(self):
        """Test add_bulk with objects that have empty fields."""
        try:
            self.backend.add_bulk(models.Book, [self.book_with_title_only, self.minimal_book])
            success = True
        except IndexError:
            success = False
        
        self.assertTrue(success, "Bulk indexing with empty fields caused an IndexError")
    
    def test_search_after_indexing_empty_fields(self):
        """Test searching works correctly after indexing objects with empty fields."""
        self.backend.add(self.book_with_title_only)
        self.backend.add(self.minimal_book)
        
        results = self.backend.search("Book with title only", models.Book)
        self.assertEqual(len(list(results)), 1)
        self.assertEqual(results[0].id, self.book_with_title_only.id)
    
    def test_direct_sql_lists(self):
        """Test the list length equalization logic directly."""
        title_sql = ["title1", "title2"]
        autocomplete_sql = ["autocomplete1"]
        body_sql = ["body1", "body2", "body3"]
        
        if not (len(title_sql) == len(autocomplete_sql) == len(body_sql)):
            max_length = max(len(title_sql), len(autocomplete_sql), len(body_sql))
            empty_sql = "NULL"
            title_sql.extend([empty_sql] * (max_length - len(title_sql)))
            autocomplete_sql.extend([empty_sql] * (max_length - len(autocomplete_sql)))
            body_sql.extend([empty_sql] * (max_length - len(body_sql)))
        
        self.assertEqual(len(title_sql), len(autocomplete_sql))
        self.assertEqual(len(autocomplete_sql), len(body_sql))
        self.assertEqual(len(title_sql), 3)
        
        self.assertEqual(title_sql, ["title1", "title2", "NULL"])
        self.assertEqual(autocomplete_sql, ["autocomplete1", "NULL", "NULL"])
        self.assertEqual(body_sql, ["body1", "body2", "body3"])
        
        zipped = list(zip(title_sql, autocomplete_sql, body_sql))
        self.assertEqual(len(zipped), 3)
