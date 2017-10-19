from __future__ import absolute_import, unicode_literals

from datetime import date

from django.core import management
from django.utils.six import StringIO

from wagtail.tests.search import models


class ElasticsearchCommonSearchBackendTests(object):
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
        from wagtail.wagtailsearch.backends.base import FilterError

        with self.assertRaises(FilterError):
            list(self.backend.search("Hello", models.Book.objects.filter(title__iregex='h(ea)llo')))

    def test_partial_search(self):
        results = self.backend.search("Java", models.Book)

        self.assertEqual(set(r.title for r in results), {
            "JavaScript: The Definitive Guide",
            "JavaScript: The good parts"
        })

    def test_child_partial_search(self):
        # Note: Expands to "Westeros". Which is in a field on Novel.setting
        results = self.backend.search("Wes", models.Book)

        self.assertEqual(set(r.title for r in results), {
            "A Game of Thrones",
            "A Storm of Swords",
            "A Clash of Kings"
        })

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

        self.assertEqual(set(r.title for r in results), {
            "Ĥéllø"
        })

    def test_query_analyser(self):
        # This is testing that fields that use edgengram_analyzer as their index analyser do not
        # have it also as their query analyser
        results = self.backend.search("JavaScript", models.Book)
        self.assertEqual(set(r.title for r in results), {
            "JavaScript: The Definitive Guide",
            "JavaScript: The good parts"
        })

        # Even though they both start with "Java", this should not match the "JavaScript" books
        results = self.backend.search("JavaBeans", models.Book)
        self.assertEqual(set(r.title for r in results), {})

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
        self.assertEqual(set(r.title for r in results), {
            "Harry Potter and the Half-Blood Prince",
        })

    def test_and_operator_with_single_field(self):
        # Testing for bug #1859
        results = self.backend.search("JavaScript", models.Book, operator='and', fields=['title'])
        self.assertEqual(set(r.title for r in results), {
            "JavaScript: The Definitive Guide",
            "JavaScript: The good parts"
        })

    def test_update_index_command_schema_only(self):
        management.call_command(
            'update_index', backend_name=self.backend_name, schema_only=True, interactive=False, stdout=StringIO()
        )

        # This should not give any results
        results = self.backend.search(None, models.Book)
        self.assertEqual(set(results), set())

    def test_annotate_score(self):
        results = self.backend.search("JavaScript", models.Book).annotate_score('_score')

        for result in results:
            self.assertIsInstance(result._score, float)

    def test_annotate_score_with_slice(self):
        # #3431 - Annotate score wasn't being passed to new queryset when slicing
        results = self.backend.search("JavaScript", models.Book).annotate_score('_score')[:10]

        for result in results:
            self.assertIsInstance(result._score, float)
