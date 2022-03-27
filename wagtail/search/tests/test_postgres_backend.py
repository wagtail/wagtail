import unittest

from django.db import connection
from django.test import TestCase
from django.test.utils import override_settings

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

    def test_index_without_upsert(self):
        # Test the add_items code path for Postgres 9.4, where upsert is not available
        self.backend.reset_index()

        index = self.backend.get_index_for_model(models.Book)
        index._enable_upsert = False
        index.add_items(models.Book, models.Book.objects.all())

        results = self.backend.search("JavaScript", models.Book)
        self.assertUnsortedListEqual(
            [r.title for r in results],
            ["JavaScript: The good parts", "JavaScript: The Definitive Guide"],
        )
