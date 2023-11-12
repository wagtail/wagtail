from datetime import date
from io import StringIO

from django.core import management

from wagtail.search.backends.base import FieldError
from wagtail.search.query import (
    MATCH_ALL,
    Boost,
    Fuzzy,
    Phrase,
    PlainText,
)
from wagtail.search.tests.test_backends import BackendTests
from wagtail.test.search import models


class ElasticsearchCommonSearchBackendTests(BackendTests):
    def test_search_with_spaces_only(self):
        # Search for some space characters and hope it doesn't crash
        results = self.backend.search("   ", models.Book)

        # Queries are lazily evaluated, force it to run
        list(results)

        # Didn't crash, yay!

    def test_filter_with_unsupported_lookup_type(self):
        """
        Not all lookup types are supported by the Elasticsearch backends
        """
        from wagtail.search.backends.base import FilterError

        with self.assertRaises(FilterError):
            list(
                self.backend.search(
                    "Hello", models.Book.objects.filter(title__iregex="h(ea)llo")
                )
            )

    def test_partial_search(self):
        results = self.backend.autocomplete("Java", models.Book)

        self.assertUnsortedListEqual(
            [r.title for r in results],
            ["JavaScript: The Definitive Guide", "JavaScript: The good parts"],
        )

    def test_disabled_partial_search(self):
        results = self.backend.search("Java", models.Book)

        self.assertUnsortedListEqual([r.title for r in results], [])

    def test_disabled_partial_search_with_whole_term(self):
        # Making sure that there isn't a different reason why the above test
        # returned no results
        results = self.backend.search("JavaScript", models.Book)

        self.assertUnsortedListEqual(
            [r.title for r in results],
            ["JavaScript: The Definitive Guide", "JavaScript: The good parts"],
        )

    def test_child_partial_search(self):
        # Note: Expands to "Westeros". Which is in a field on Novel.setting
        results = self.backend.autocomplete("Wes", models.Book)

        self.assertUnsortedListEqual(
            [r.title for r in results],
            ["A Game of Thrones", "A Storm of Swords", "A Clash of Kings"],
        )

    def test_ascii_folding(self):
        book = models.Book.objects.create(
            title="Ĥéllø", publication_date=date(2017, 10, 19), number_of_pages=1
        )

        index = self.backend.get_index_for_model(models.Book)
        index.add_item(book)
        index.refresh()

        results = self.backend.autocomplete("Hello", models.Book)

        self.assertUnsortedListEqual([r.title for r in results], ["Ĥéllø"])

    def test_query_analyser(self):
        # This is testing that fields that use edgengram_analyzer as their index analyser do not
        # have it also as their query analyser
        results = self.backend.search("JavaScript", models.Book)
        self.assertUnsortedListEqual(
            [r.title for r in results],
            ["JavaScript: The Definitive Guide", "JavaScript: The good parts"],
        )

        # Even though they both start with "Java", this should not match the "JavaScript" books
        results = self.backend.search("JavaBeans", models.Book)
        self.assertSetEqual({r.title for r in results}, set())

    def test_search_with_hyphen(self):
        """
        This tests that punctuation characters are treated the same
        way in both indexing and querying.

        See: https://github.com/wagtail/wagtail/issues/937
        """
        book = models.Book.objects.create(
            title="Harry Potter and the Half-Blood Prince",
            publication_date=date(2009, 7, 15),
            number_of_pages=607,
        )

        index = self.backend.get_index_for_model(models.Book)
        index.add_item(book)
        index.refresh()

        results = self.backend.search("Half-Blood", models.Book)
        self.assertUnsortedListEqual(
            [r.title for r in results],
            [
                "Harry Potter and the Half-Blood Prince",
            ],
        )

    def test_and_operator_with_single_field(self):
        # Testing for bug #1859
        results = self.backend.search(
            "JavaScript", models.Book, operator="and", fields=["title"]
        )
        self.assertUnsortedListEqual(
            [r.title for r in results],
            ["JavaScript: The Definitive Guide", "JavaScript: The good parts"],
        )

    def test_update_index_command_schema_only(self):
        management.call_command(
            "update_index",
            backend_name=self.backend_name,
            schema_only=True,
            stdout=StringIO(),
        )

        # This should not give any results
        results = self.backend.search(MATCH_ALL, models.Book)
        self.assertSetEqual(set(results), set())

    def test_more_than_ten_results(self):
        # #3431 reported that Elasticsearch only sends back 10 results if the results set is not sliced
        results = self.backend.search(MATCH_ALL, models.Book)

        self.assertEqual(len(results), 14)

    def test_more_than_one_hundred_results(self):
        # Tests that fetching more than 100 results uses the scroll API
        books = []
        for i in range(150):
            books.append(
                models.Book.objects.create(
                    title=f"Book {i}",
                    publication_date=date(2017, 10, 21),
                    number_of_pages=i,
                )
            )

        index = self.backend.get_index_for_model(models.Book)
        index.add_items(models.Book, books)
        index.refresh()

        results = self.backend.search(MATCH_ALL, models.Book)
        self.assertEqual(len(results), 164)

    def test_slice_more_than_one_hundred_results(self):
        books = []
        for i in range(150):
            books.append(
                models.Book.objects.create(
                    title=f"Book {i}",
                    publication_date=date(2017, 10, 21),
                    number_of_pages=i,
                )
            )

        index = self.backend.get_index_for_model(models.Book)
        index.add_items(models.Book, books)
        index.refresh()

        results = self.backend.search(MATCH_ALL, models.Book)[10:120]
        self.assertEqual(len(results), 110)

    def test_slice_to_next_page(self):
        # ES scroll API doesn't support offset. The implementation has an optimisation
        # which will skip the first page if the first result is on the second page
        books = []
        for i in range(150):
            books.append(
                models.Book.objects.create(
                    title=f"Book {i}",
                    publication_date=date(2017, 10, 21),
                    number_of_pages=i,
                )
            )

        index = self.backend.get_index_for_model(models.Book)
        index.add_items(models.Book, books)
        index.refresh()

        results = self.backend.search(MATCH_ALL, models.Book)[110:]
        self.assertEqual(len(results), 54)

    def test_cannot_filter_on_date_parts_other_than_year(self):
        # Filtering by date not supported, should throw a FilterError
        from wagtail.search.backends.base import FilterError

        in_jan = models.Book.objects.filter(publication_date__month=1)
        with self.assertRaises(FilterError):
            self.backend.search(MATCH_ALL, in_jan)

    # QUERY FIELD PARAMETER TESTS

    def test_search_one_field_arg_empty(self):
        query = PlainText("Westeros", fields=[]) & Phrase(
            "Game of Thrones", fields=["title"]
        )
        results = self.backend.search(query, models.Novel)
        self.assertEqual(len(results), 0)

    def test_search_on_individual_field_arg(self):
        # The following query shouldn't search the Novel.setting field so none
        # of the Novels set in "Westeros" should be returned
        results = self.backend.search(
            PlainText("Westeros Hobbit", fields=["title"], operator="or"), models.Book
        )

        self.assertUnsortedListEqual([r.title for r in results], ["The Hobbit"])

    def test_search_on_unknown_field_arg(self):
        with self.assertRaises(FieldError):
            list(
                self.backend.search(
                    PlainText("Westeros Hobbit", fields=["unknown"], operator="or"),
                    models.Book,
                )
            )

    def test_search_on_non_searchable_field_arg(self):
        with self.assertRaises(FieldError):
            list(
                self.backend.search(
                    PlainText(
                        "Westeros Hobbit",
                        fields=["number_of_pages"],
                        operator="or",
                    ),
                    models.Book,
                )
            )

    def test_search_on_multiple_field_arg(self):
        results = self.backend.search(
            PlainText("Westeros Thrones", fields=["title", "setting"], operator="or"),
            models.Novel,
        )

        self.assertUnsortedListEqual(
            [r.title for r in results],
            ["A Clash of Kings", "A Game of Thrones", "A Storm of Swords"],
        )

    def test_search_on_multiple_queries_with_and_fields(self):
        query = PlainText("Westeros", fields=["setting", "title"]) & Phrase(
            "Game of Thrones", fields=["title"]
        )
        results = self.backend.search(query, models.Novel)

        self.assertUnsortedListEqual([r.title for r in results], ["A Game of Thrones"])

    def test_search_on_multiple_queries_with_or_fields(self):
        query = PlainText("Westeros", fields=["setting"]) | Phrase(
            "The Hobbit", fields=["title"]
        )
        results = self.backend.search(query, models.Novel)

        self.assertUnsortedListEqual(
            [r.title for r in results],
            [
                "A Clash of Kings",
                "A Game of Thrones",
                "A Storm of Swords",
                "The Hobbit",
            ],
        )

    def test_search_on_multiple_queries_with_not_fields(self):
        query = PlainText("Westeros", fields=["setting", "title"]) & ~PlainText(
            "Thrones", fields=["title"]
        )
        results = self.backend.search(query, models.Novel)

        self.assertUnsortedListEqual(
            [r.title for r in results],
            [
                "A Clash of Kings",
                "A Storm of Swords",
            ],
        )

    def test_search_fuzzy_with_field_arg(self):
        query = Fuzzy("Westerop", fields=["setting"]) & PlainText(
            "Thrones", fields=["title"]
        )
        results = self.backend.search(query, models.Novel)

        self.assertUnsortedListEqual([r.title for r in results], ["A Game of Thrones"])

    def test_search_field_arg_override(self):
        # the `fields` param in the query takes precidence over the value given to `search`
        query = PlainText("Westeros", fields=["setting"], operator="and") & PlainText(
            "Thrones"
        )
        results = self.backend.search(query, models.Novel, fields=["title"])

        self.assertUnsortedListEqual([r.title for r in results], ["A Game of Thrones"])

    def test_boost_with_fields(self):
        results = self.backend.search(
            PlainText("JavaScript Definitive", fields=["title"])
            | Boost(PlainText("Learning Python", fields=["title"]), 2.0),
            models.Book.objects.all(),
        )

        # Both python and JavaScript should be returned with Python at the top
        self.assertEqual(
            [r.title for r in results],
            [
                "Learning Python",
                "JavaScript: The Definitive Guide",
            ],
        )

        results = self.backend.search(
            PlainText("JavaScript Definitive", fields=["title"])
            | Boost(PlainText("Learning Python", fields=["title"]), 0.5),
            models.Book.objects.all(),
        )

        # Now they should be swapped
        self.assertEqual(
            [r.title for r in results],
            [
                "JavaScript: The Definitive Guide",
                "Learning Python",
            ],
        )

    def test_autocomplete_with_fields_arg_in_query(self):
        results = self.backend.autocomplete(
            PlainText("Georg", fields=["name"]), models.Author
        )
        self.assertUnsortedListEqual(
            [r.name for r in results],
            [
                "George R.R. Martin",
            ],
        )
