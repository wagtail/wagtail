import unittest

from datetime import date
from io import StringIO

from django.core import management

from wagtail.search.query import MATCH_ALL
from wagtail.search.tests.test_backends import BackendTests
from wagtail.tests.search import models


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
            list(self.backend.search("Hello", models.Book.objects.filter(title__iregex='h(ea)llo')))

    def test_partial_search(self):
        results = self.backend.search("Java", models.Book)

        self.assertUnsortedListEqual([r.title for r in results], [
            "JavaScript: The Definitive Guide",
            "JavaScript: The good parts"
        ])

    def test_disabled_partial_search(self):
        results = self.backend.search("Java", models.Book, partial_match=False)

        self.assertUnsortedListEqual([r.title for r in results], [])

    def test_disabled_partial_search_with_whole_term(self):
        # Making sure that there isn't a different reason why the above test
        # returned no results
        results = self.backend.search("JavaScript", models.Book, partial_match=False)

        self.assertUnsortedListEqual([r.title for r in results], [
            "JavaScript: The Definitive Guide",
            "JavaScript: The good parts"
        ])

    def test_child_partial_search(self):
        # Note: Expands to "Westeros". Which is in a field on Novel.setting
        results = self.backend.search("Wes", models.Book)

        self.assertUnsortedListEqual([r.title for r in results], [
            "A Game of Thrones",
            "A Storm of Swords",
            "A Clash of Kings"
        ])

    def test_ascii_folding(self):
        book = models.Book.objects.create(
            title="Ĥéllø",
            publication_date=date(2017, 10, 19),
            number_of_pages=1
        )

        index = self.backend.get_index_for_model(models.Book)
        index.add_item(book)
        index.refresh()

        results = self.backend.search("Hello", models.Book)

        self.assertUnsortedListEqual([r.title for r in results], [
            "Ĥéllø"
        ])

    def test_query_analyser(self):
        # This is testing that fields that use edgengram_analyzer as their index analyser do not
        # have it also as their query analyser
        results = self.backend.search("JavaScript", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [
            "JavaScript: The Definitive Guide",
            "JavaScript: The good parts"
        ])

        # Even though they both start with "Java", this should not match the "JavaScript" books
        results = self.backend.search("JavaBeans", models.Book)
        self.assertSetEqual(set(r.title for r in results), set())

    def test_search_with_hyphen(self):
        """
        This tests that punctuation characters are treated the same
        way in both indexing and querying.

        See: https://github.com/wagtail/wagtail/issues/937
        """
        book = models.Book.objects.create(
            title="Harry Potter and the Half-Blood Prince",
            publication_date=date(2009, 7, 15),
            number_of_pages=607
        )

        index = self.backend.get_index_for_model(models.Book)
        index.add_item(book)
        index.refresh()

        results = self.backend.search("Half-Blood", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [
            "Harry Potter and the Half-Blood Prince",
        ])

    def test_and_operator_with_single_field(self):
        # Testing for bug #1859
        results = self.backend.search("JavaScript", models.Book, operator='and', fields=['title'])
        self.assertUnsortedListEqual([r.title for r in results], [
            "JavaScript: The Definitive Guide",
            "JavaScript: The good parts"
        ])

    def test_update_index_command_schema_only(self):
        management.call_command(
            'update_index', backend_name=self.backend_name, schema_only=True, stdout=StringIO()
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
            books.append(models.Book.objects.create(title="Book {}".format(i), publication_date=date(2017, 10, 21), number_of_pages=i))

        index = self.backend.get_index_for_model(models.Book)
        index.add_items(models.Book, books)
        index.refresh()

        results = self.backend.search(MATCH_ALL, models.Book)
        self.assertEqual(len(results), 164)

    def test_slice_more_than_one_hundred_results(self):
        books = []
        for i in range(150):
            books.append(models.Book.objects.create(title="Book {}".format(i), publication_date=date(2017, 10, 21), number_of_pages=i))

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
            books.append(models.Book.objects.create(title="Book {}".format(i), publication_date=date(2017, 10, 21), number_of_pages=i))

        index = self.backend.get_index_for_model(models.Book)
        index.add_items(models.Book, books)
        index.refresh()

        results = self.backend.search(MATCH_ALL, models.Book)[110:]
        self.assertEqual(len(results), 54)

    # Elasticsearch always does prefix matching on `partial_match` fields,
    # even when we don’t use `Prefix`.
    @unittest.expectedFailure
    def test_incomplete_term(self):
        super().test_incomplete_term()

    # Elasticsearch does not accept prefix for multiple words
    @unittest.expectedFailure
    def test_prefix_multiple_words(self):
        super().test_prefix_multiple_words()

    # Elasticsearch always does prefix matching on `partial_match` fields,
    # even when we don’t use `Prefix`.
    @unittest.expectedFailure
    def test_incomplete_plain_text(self):
        super().test_incomplete_plain_text()

    # Elasticsearch does not support 'fields' arguments on autocomplete queries
    @unittest.expectedFailure
    def test_autocomplete_with_fields_arg(self):
        super().test_autocomplete_with_fields_arg()
