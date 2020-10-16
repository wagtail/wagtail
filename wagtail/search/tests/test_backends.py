# coding: utf-8

import unittest

from collections import OrderedDict
from datetime import date
from io import StringIO

from django.conf import settings
from django.core import management
from django.test import TestCase
from django.test.utils import override_settings
from taggit.models import Tag

from wagtail.search.backends import (
    InvalidSearchBackendError, get_search_backend, get_search_backends)
from wagtail.search.backends.base import FieldError, FilterFieldError
from wagtail.search.backends.db import DatabaseSearchBackend
from wagtail.search.query import MATCH_ALL, MATCH_NONE, And, Boost, Not, Or, Phrase, PlainText
from wagtail.tests.search import models
from wagtail.tests.utils import WagtailTestUtils


class BackendTests(WagtailTestUtils):
    # To test a specific backend, subclass BackendTests and define self.backend_path.

    fixtures = ['search']

    def setUp(self):
        # Search WAGTAILSEARCH_BACKENDS for an entry that uses the given backend path
        for backend_name, backend_conf in settings.WAGTAILSEARCH_BACKENDS.items():
            if backend_conf['BACKEND'] == self.backend_path:
                self.backend = get_search_backend(backend_name)
                self.backend_name = backend_name
                break
        else:
            # no conf entry found - skip tests for this backend
            raise unittest.SkipTest("No WAGTAILSEARCH_BACKENDS entry for the backend %s" % self.backend_path)

        management.call_command('update_index', backend_name=self.backend_name, stdout=StringIO(), chunk_size=50)

    def assertUnsortedListEqual(self, a, b):
        """
        Checks two results lists are equal while not taking into account the ordering.

        Note: This is different to assertSetEqual in that duplicate results are taken
        into account.
        """
        self.assertListEqual(list(sorted(a)), list(sorted(b)))

    # SEARCH TESTS

    def test_search_simple(self):
        results = self.backend.search("JavaScript", models.Book)
        self.assertUnsortedListEqual([r.title for r in results], [
            "JavaScript: The good parts",
            "JavaScript: The Definitive Guide"
        ])

    def test_search_count(self):
        results = self.backend.search("JavaScript", models.Book)
        self.assertEqual(results.count(), 2)

    def test_search_blank(self):
        # Blank searches should never return anything
        results = self.backend.search("", models.Book)
        self.assertSetEqual(set(results), set())

    def test_search_all(self):
        results = self.backend.search(MATCH_ALL, models.Book)
        self.assertSetEqual(set(results), set(models.Book.objects.all()))

    def test_search_none(self):
        results = self.backend.search(MATCH_NONE, models.Book)
        self.assertFalse(list(results))

    def test_ranking(self):
        # Note: also tests the "or" operator
        results = list(self.backend.search("JavaScript Definitive", models.Book, operator='or'))
        self.assertUnsortedListEqual([r.title for r in results], [
            "JavaScript: The good parts",
            "JavaScript: The Definitive Guide"
        ])

        # "JavaScript: The Definitive Guide" should be first
        self.assertEqual(results[0].title, "JavaScript: The Definitive Guide")

    def test_annotate_score(self):
        results = self.backend.search("JavaScript", models.Book).annotate_score('_score')

        for result in results:
            self.assertIsInstance(result._score, float)

    def test_annotate_score_with_slice(self):
        # #3431 - Annotate score wasn't being passed to new queryset when slicing
        results = self.backend.search("JavaScript", models.Book).annotate_score('_score')[:10]

        for result in results:
            self.assertIsInstance(result._score, float)

    def test_search_and_operator(self):
        # Should not return "JavaScript: The good parts" as it does not have "Definitive"
        results = self.backend.search("JavaScript Definitive", models.Book, operator='and')
        self.assertUnsortedListEqual([r.title for r in results], [
            "JavaScript: The Definitive Guide"
        ])

    def test_search_on_child_class(self):
        # Searches on a child class should only return results that have the child class as well
        # and all results should be instances of the child class
        results = self.backend.search(MATCH_ALL, models.Novel)
        self.assertSetEqual(set(results), set(models.Novel.objects.all()))

    def test_search_child_class_field_from_parent(self):
        # Searches the Book model for content that exists in the Novel model
        # Note: "Westeros" only occurs in the Novel.setting field
        # All results should be instances of the parent class
        results = self.backend.search("Westeros", models.Book)

        self.assertUnsortedListEqual([r.title for r in results], [
            "A Game of Thrones",
            "A Clash of Kings",
            "A Storm of Swords"
        ])

        self.assertIsInstance(results[0], models.Book)

    def test_search_on_individual_field(self):
        # The following query shouldn't search the Novel.setting field so none
        # of the Novels set in "Westeros" should be returned
        results = self.backend.search("Westeros Hobbit", models.Book, fields=['title'], operator='or')

        self.assertUnsortedListEqual([r.title for r in results], [
            "The Hobbit"
        ])

    def test_search_on_unknown_field(self):
        with self.assertRaises(FieldError):
            list(self.backend.search("Westeros Hobbit", models.Book, fields=['unknown'], operator='or'))

    def test_search_on_non_searchable_field(self):
        with self.assertRaises(FieldError):
            list(self.backend.search("Westeros Hobbit", models.Book, fields=['number_of_pages'], operator='or'))

    def test_search_on_related_fields(self):
        results = self.backend.search("Bilbo Baggins", models.Novel)

        self.assertUnsortedListEqual([r.title for r in results], [
            "The Hobbit",
            "The Fellowship of the Ring",
            "The Two Towers",
            "The Return of the King"
        ])

    def test_search_boosting_on_related_fields(self):
        # Bilbo Baggins is the protagonist of "The Hobbit" but not any of the "Lord of the Rings" novels.
        # As the protagonist has more boost than other characters, "The Hobbit" should always be returned
        # first
        results = list(self.backend.search("Bilbo Baggins", models.Novel))

        self.assertEqual(results[0].title, "The Hobbit")

        # The remaining results should be scored equally so their rank is undefined
        self.assertUnsortedListEqual([r.title for r in results[1:]], [
            "The Fellowship of the Ring",
            "The Two Towers",
            "The Return of the King"
        ])

    def test_search_callable_field(self):
        # "Django Two scoops" only mentions "Python" in its "get_programming_language_display"
        # callable field
        results = self.backend.search("Python", models.Book)

        self.assertUnsortedListEqual([r.title for r in results], [
            "Learning Python",
            "Two Scoops of Django 1.11"
        ])

    # AUTOCOMPLETE TESTS

    def test_autocomplete(self):
        # This one shouldn't match "Django Two scoops" as "get_programming_language_display"
        # isn't an autocomplete field
        results = self.backend.autocomplete("Py", models.Book)

        self.assertUnsortedListEqual([r.title for r in results], [
            "Learning Python",
        ])

    def test_autocomplete_uses_autocompletefield(self):
        # Autocomplete should only require an AutocompleteField, not a SearchField with
        # partial_match=True
        results = self.backend.autocomplete("Georg", models.Author)
        self.assertUnsortedListEqual([r.name for r in results], [
            "George R.R. Martin",
        ])

    def test_autocomplete_with_fields_arg(self):
        results = self.backend.autocomplete("Georg", models.Author, fields=['name'])
        self.assertUnsortedListEqual([r.name for r in results], [
            "George R.R. Martin",
        ])

    def test_autocomplete_not_affected_by_stemming(self):
        # If SEARCH_CONFIG is set, stemming will be enabled.
        # But we want to disable this for autocomplete as stemmed words don't always match on prefixes
        # See: https://www.postgresql.org/docs/9.1/datatype-textsearch.html#DATATYPE-TSQUERY
        results = self.backend.autocomplete("Learni", models.Book)

        self.assertUnsortedListEqual([r.title for r in results], [
            "Learning Python",
        ])

    # FILTERING TESTS

    def test_filter_exact_value(self):
        results = self.backend.search(MATCH_ALL, models.Book.objects.filter(number_of_pages=440))

        self.assertUnsortedListEqual([r.title for r in results], [
            "The Return of the King",
            "The Rust Programming Language"
        ])

    def test_filter_exact_value_on_parent_model_field(self):
        results = self.backend.search(MATCH_ALL, models.Novel.objects.filter(number_of_pages=440))

        self.assertUnsortedListEqual([r.title for r in results], [
            "The Return of the King"
        ])

    def test_filter_lt(self):
        results = self.backend.search(MATCH_ALL, models.Book.objects.filter(number_of_pages__lt=440))

        self.assertUnsortedListEqual([r.title for r in results], [
            "The Hobbit",
            "JavaScript: The good parts",
            "The Fellowship of the Ring",
            "Foundation",
            "The Two Towers"
        ])

    def test_filter_lte(self):
        results = self.backend.search(MATCH_ALL, models.Book.objects.filter(number_of_pages__lte=440))

        self.assertUnsortedListEqual([r.title for r in results], [
            "The Return of the King",
            "The Rust Programming Language",
            "The Hobbit",
            "JavaScript: The good parts",
            "The Fellowship of the Ring",
            "Foundation",
            "The Two Towers"
        ])

    def test_filter_gt(self):
        results = self.backend.search(MATCH_ALL, models.Book.objects.filter(number_of_pages__gt=440))

        self.assertUnsortedListEqual([r.title for r in results], [
            "JavaScript: The Definitive Guide",
            "Learning Python",
            "A Clash of Kings",
            "A Game of Thrones",
            "Two Scoops of Django 1.11",
            "A Storm of Swords",
            "Programming Rust",
        ])

    def test_filter_gte(self):
        results = self.backend.search(MATCH_ALL, models.Book.objects.filter(number_of_pages__gte=440))

        self.assertUnsortedListEqual([r.title for r in results], [
            "The Return of the King",
            "The Rust Programming Language",
            "JavaScript: The Definitive Guide",
            "Learning Python",
            "A Clash of Kings",
            "A Game of Thrones",
            "Two Scoops of Django 1.11",
            "A Storm of Swords",
            "Programming Rust",
        ])

    def test_filter_in_list(self):
        results = self.backend.search(MATCH_ALL, models.Book.objects.filter(number_of_pages__in=[440, 1160]))

        self.assertUnsortedListEqual([r.title for r in results], [
            "The Return of the King",
            "The Rust Programming Language",
            "Learning Python"
        ])

    def test_filter_in_iterable(self):
        results = self.backend.search(MATCH_ALL, models.Book.objects.filter(number_of_pages__in=iter([440, 1160])))

        self.assertUnsortedListEqual([r.title for r in results], [
            "The Return of the King",
            "The Rust Programming Language",
            "Learning Python"
        ])

    def test_filter_in_values_list_subquery(self):
        values = models.Book.objects.filter(number_of_pages__lt=440).values_list('number_of_pages', flat=True)
        results = self.backend.search(MATCH_ALL, models.Book.objects.filter(number_of_pages__in=values))

        self.assertUnsortedListEqual([r.title for r in results], [
            "The Hobbit",
            "JavaScript: The good parts",
            "The Fellowship of the Ring",
            "Foundation",
            "The Two Towers"
        ])

    def test_filter_isnull_true(self):
        # Note: We don't know the birth dates of any of the programming guide authors
        results = self.backend.search(MATCH_ALL, models.Author.objects.filter(date_of_birth__isnull=True))

        self.assertUnsortedListEqual([r.name for r in results], [
            "David Ascher",
            "Mark Lutz",
            "David Flanagan",
            "Douglas Crockford",
            "Daniel Roy Greenfeld",
            "Audrey Roy Greenfeld",
            "Carol Nichols",
            "Steve Klabnik",
            "Jim Blandy",
            "Jason Orendorff",
        ])

    def test_filter_isnull_false(self):
        # Note: We know the birth dates of all of the novel authors
        results = self.backend.search(MATCH_ALL, models.Author.objects.filter(date_of_birth__isnull=False))

        self.assertUnsortedListEqual([r.name for r in results], [
            "Isaac Asimov",
            "George R.R. Martin",
            "J. R. R. Tolkien"
        ])

    def test_filter_prefix(self):
        results = self.backend.search(MATCH_ALL, models.Book.objects.filter(title__startswith="Th"))

        self.assertUnsortedListEqual([r.title for r in results], [
            "The Hobbit",
            "The Fellowship of the Ring",
            "The Two Towers",
            "The Return of the King",
            "The Rust Programming Language"
        ])

    def test_filter_and_operator(self):
        results = self.backend.search(
            MATCH_ALL, models.Book.objects.filter(number_of_pages=440) & models.Book.objects.filter(publication_date=date(1955, 10, 20)))

        self.assertUnsortedListEqual([r.title for r in results], [
            "The Return of the King"
        ])

    def test_filter_or_operator(self):
        results = self.backend.search(MATCH_ALL, models.Book.objects.filter(number_of_pages=440) | models.Book.objects.filter(number_of_pages=1160))

        self.assertUnsortedListEqual([r.title for r in results], [
            "Learning Python",
            "The Return of the King",
            "The Rust Programming Language"
        ])

    def test_filter_on_non_filterable_field(self):
        with self.assertRaises(FieldError):
            list(self.backend.search(MATCH_ALL, models.Author.objects.filter(name__startswith="Issac")))

    # ORDER BY RELEVANCE

    def test_order_by_relevance(self):
        results = self.backend.search(MATCH_ALL, models.Novel.objects.order_by('number_of_pages'), order_by_relevance=False)

        # Ordering should be set to "number_of_pages"
        self.assertEqual([r.title for r in results], [
            "Foundation",
            "The Hobbit",
            "The Two Towers",
            "The Fellowship of the Ring",
            "The Return of the King",
            "A Game of Thrones",
            "A Clash of Kings",
            "A Storm of Swords"
        ])

    def test_order_by_non_filterable_field(self):
        with self.assertRaises(FieldError):
            list(self.backend.search(MATCH_ALL, models.Author.objects.order_by('name'), order_by_relevance=False))

    # SLICING TESTS

    def test_single_result(self):
        results = self.backend.search(MATCH_ALL, models.Novel.objects.order_by('number_of_pages'), order_by_relevance=False)

        self.assertEqual(results[0].title, "Foundation")
        self.assertEqual(results[1].title, "The Hobbit")

    def test_limit(self):
        # Note: we need consistent ordering for this test
        results = self.backend.search(MATCH_ALL, models.Novel.objects.order_by('number_of_pages'), order_by_relevance=False)

        # Limit the results
        results = results[:3]

        self.assertListEqual([r.title for r in results], [
            "Foundation",
            "The Hobbit",
            "The Two Towers"
        ])

    def test_offset(self):
        # Note: we need consistent ordering for this test
        results = self.backend.search(MATCH_ALL, models.Novel.objects.order_by('number_of_pages'), order_by_relevance=False)

        # Offset the results
        results = results[3:]

        self.assertListEqual(list(r.title for r in results), [
            "The Fellowship of the Ring",
            "The Return of the King",
            "A Game of Thrones",
            "A Clash of Kings",
            "A Storm of Swords"
        ])

    def test_offset_and_limit(self):
        # Note: we need consistent ordering for this test
        results = self.backend.search(MATCH_ALL, models.Novel.objects.order_by('number_of_pages'), order_by_relevance=False)

        # Offset the results
        results = results[3:6]

        self.assertListEqual([r.title for r in results], [
            "The Fellowship of the Ring",
            "The Return of the King",
            "A Game of Thrones"
        ])

    # FACET TESTS

    def test_facet(self):
        results = self.backend.search(MATCH_ALL, models.ProgrammingGuide).facet('programming_language')

        # Not testing ordering here as two of the items have the same count, so the ordering is undefined.
        # See test_facet_tags for a test of the ordering
        self.assertDictEqual(dict(results), {'js': 2, 'py': 2, 'rs': 1})

    def test_facet_tags(self):
        # The test data doesn't contain any tags, add some
        FANTASY_BOOKS = [1, 2, 3, 4, 5, 6, 7]
        SCIFI_BOOKS = [10]
        for book in models.Book.objects.filter(id__in=FANTASY_BOOKS + SCIFI_BOOKS):
            book = book.get_indexed_instance()

            if book.id in FANTASY_BOOKS:
                book.tags.add('Fantasy')
            if book.id in SCIFI_BOOKS:
                book.tags.add('Science Fiction')

            self.backend.add(book)

        index = self.backend.get_index_for_model(models.Book)
        if index:
            index.refresh()

        fantasy_tag = Tag.objects.get(name='Fantasy')
        scifi_tag = Tag.objects.get(name='Science Fiction')

        results = self.backend.search(MATCH_ALL, models.Book).facet('tags')

        self.assertEqual(results, OrderedDict([
            (fantasy_tag.id, 7),
            (None, 6),
            (scifi_tag.id, 1),
        ]))

    def test_facet_with_nonexistent_field(self):
        with self.assertRaises(FilterFieldError):
            self.backend.search(MATCH_ALL, models.ProgrammingGuide).facet('foo')

    # MISC TESTS

    def test_same_rank_pages(self):
        # Checks that results with a same ranking cannot be found multiple times
        # across pages (see issue #3729).
        same_rank_objects = set()

        index = self.backend.get_index_for_model(models.Book)
        for i in range(10):
            obj = models.Book.objects.create(title='Rank %s' % i, publication_date=date(2017, 10, 18), number_of_pages=100)
            index.add_item(obj)
            same_rank_objects.add(obj)
        index.refresh()

        results = self.backend.search('Rank', models.Book)
        results_across_pages = set()
        for i, obj in enumerate(same_rank_objects):
            results_across_pages.add(results[i:i + 1][0])
        self.assertSetEqual(results_across_pages, same_rank_objects)

    def test_delete(self):
        foundation = models.Novel.objects.filter(title="Foundation").first()

        # Delete from the search index
        index = self.backend.get_index_for_model(models.Novel)
        if index:
            index.delete_item(foundation)
            index.refresh()

        # Delete from the database
        foundation.delete()

        # To test that the book was deleted from the index as well, we will perform the slicing check from an earlier
        # test where "Foundation" was the first result. We need to test it this way so we can pick up the case where
        # the object still exists in the index but not in the database (in that case, just two objects would be returned
        # instead of three).

        # Note: we need consistent ordering for this test
        results = self.backend.search(MATCH_ALL, models.Novel.objects.order_by('number_of_pages'), order_by_relevance=False)

        # Limit the results
        results = results[:3]

        self.assertEqual(list(r.title for r in results), [
            # "Foundation"
            "The Hobbit",
            "The Two Towers",
            "The Fellowship of the Ring"  # If this item doesn't appear, "Foundation" is still in the index
        ])

    def test_plain_text_single_word(self):
        results = self.backend.search(PlainText('JavaScript'),
                                      models.Book.objects.all())
        self.assertSetEqual({r.title for r in results},
                            {'JavaScript: The Definitive Guide',
                             'JavaScript: The good parts'})

    def test_incomplete_plain_text(self):
        results = self.backend.search(PlainText('pro'),
                                      models.Book.objects.all())

        self.assertSetEqual({r.title for r in results}, set())

    def test_plain_text_multiple_words_or(self):
        results = self.backend.search(PlainText('JavaScript Definitive',
                                                operator='or'),
                                      models.Book.objects.all())
        self.assertSetEqual({r.title for r in results},
                            {'JavaScript: The Definitive Guide',
                             'JavaScript: The good parts'})

    def test_plain_text_multiple_words_and(self):
        results = self.backend.search(PlainText('JavaScript Definitive',
                                                operator='and'),
                                      models.Book.objects.all())
        self.assertSetEqual({r.title for r in results},
                            {'JavaScript: The Definitive Guide'})

    def test_plain_text_operator_case(self):
        results = self.backend.search(PlainText('Guide', operator='AND'),
                                      models.Book.objects.all())
        self.assertSetEqual({r.title for r in results},
                            {'JavaScript: The Definitive Guide'})

        results = self.backend.search(PlainText('Guide', operator='aNd'),
                                      models.Book.objects.all())
        self.assertSetEqual({r.title for r in results},
                            {'JavaScript: The Definitive Guide'})

        results = self.backend.search('Guide', models.Book.objects.all(),
                                      operator='AND')
        self.assertSetEqual({r.title for r in results},
                            {'JavaScript: The Definitive Guide'})

        results = self.backend.search('Guide', models.Book.objects.all(),
                                      operator='aNd')
        self.assertSetEqual({r.title for r in results},
                            {'JavaScript: The Definitive Guide'})

    def test_plain_text_invalid_operator(self):
        with self.assertRaises(ValueError):
            self.backend.search(PlainText('Guide', operator='xor'),
                                models.Book.objects.all())

        with self.assertRaises(ValueError):
            self.backend.search('Guide', models.Book.objects.all(),
                                operator='xor')

    def test_boost(self):
        results = self.backend.search(PlainText('JavaScript Definitive') | Boost(PlainText('Learning Python'), 2.0), models.Book.objects.all())

        # Both python and JavaScript should be returned with Python at the top
        self.assertEqual([r.title for r in results], [
            "Learning Python",
            "JavaScript: The Definitive Guide",
        ])

        results = self.backend.search(PlainText('JavaScript Definitive') | Boost(PlainText('Learning Python'), 0.5), models.Book.objects.all())

        # Now they should be swapped
        self.assertEqual([r.title for r in results], [
            "JavaScript: The Definitive Guide",
            "Learning Python",
        ])

    def test_match_all(self):
        results = self.backend.search(MATCH_ALL, models.Book.objects.all())
        self.assertEqual(len(results), 14)

    def test_and(self):
        results = self.backend.search(And([PlainText('javascript'),
                                           PlainText('definitive')]),
                                      models.Book.objects.all())
        self.assertSetEqual({r.title for r in results},
                            {'JavaScript: The Definitive Guide'})

        results = self.backend.search(PlainText('javascript') & PlainText('definitive'),
                                      models.Book.objects.all())
        self.assertSetEqual({r.title for r in results},
                            {'JavaScript: The Definitive Guide'})

    def test_or(self):
        results = self.backend.search(Or([PlainText('hobbit'), PlainText('towers')]),
                                      models.Book.objects.all())
        self.assertSetEqual({r.title for r in results},
                            {'The Hobbit', 'The Two Towers'})

        results = self.backend.search(PlainText('hobbit') | PlainText('towers'),
                                      models.Book.objects.all())
        self.assertSetEqual({r.title for r in results},
                            {'The Hobbit', 'The Two Towers'})

    def test_not(self):
        all_other_titles = {
            'A Clash of Kings',
            'A Game of Thrones',
            'A Storm of Swords',
            'Foundation',
            'Learning Python',
            'The Hobbit',
            'The Two Towers',
            'The Fellowship of the Ring',
            'The Return of the King',
            'The Rust Programming Language',
            'Two Scoops of Django 1.11',
            'Programming Rust',
        }

        results = self.backend.search(Not(PlainText('javascript')),
                                      models.Book.objects.all())
        self.assertSetEqual({r.title for r in results}, all_other_titles)

        results = self.backend.search(~PlainText('javascript'),
                                      models.Book.objects.all())
        self.assertSetEqual({r.title for r in results}, all_other_titles)

        # Tests multiple words
        results = self.backend.search(~PlainText('javascript the'),
                                      models.Book.objects.all())
        self.assertSetEqual({r.title for r in results}, all_other_titles)

    def test_operators_combination(self):
        results = self.backend.search(
            (
                (PlainText('javascript') & ~PlainText('definitive'))
                | PlainText('python') | PlainText('rust')
            ) | PlainText('two'),
            models.Book.objects.all()
        )
        self.assertSetEqual({r.title for r in results},
                            {'JavaScript: The good parts',
                             'Learning Python',
                             'The Two Towers',
                             'The Rust Programming Language',
                             'Two Scoops of Django 1.11',
                             'Programming Rust'})

    def test_phrase(self):
        results = self.backend.search(Phrase('rust programming'), models.Book.objects.all())
        self.assertSetEqual({r.title for r in results}, {'The Rust Programming Language'})

        results = self.backend.search(Phrase('programming rust'), models.Book.objects.all())
        self.assertSetEqual({r.title for r in results}, {'Programming Rust'})


@override_settings(
    WAGTAILSEARCH_BACKENDS={
        'default': {'BACKEND': 'wagtail.search.backends.db'}
    }
)
class TestBackendLoader(TestCase):
    def test_import_by_name(self):
        db = get_search_backend(backend='default')
        self.assertIsInstance(db, DatabaseSearchBackend)

    def test_import_by_path(self):
        db = get_search_backend(backend='wagtail.search.backends.db')
        self.assertIsInstance(db, DatabaseSearchBackend)

    def test_import_by_full_path(self):
        db = get_search_backend(backend='wagtail.search.backends.db.DatabaseSearchBackend')
        self.assertIsInstance(db, DatabaseSearchBackend)

    def test_nonexistent_backend_import(self):
        self.assertRaises(
            InvalidSearchBackendError, get_search_backend, backend='wagtail.search.backends.doesntexist'
        )

    def test_invalid_backend_import(self):
        self.assertRaises(InvalidSearchBackendError, get_search_backend, backend="I'm not a backend!")

    def test_get_search_backends(self):
        backends = list(get_search_backends())

        self.assertEqual(len(backends), 1)
        self.assertIsInstance(backends[0], DatabaseSearchBackend)

    @override_settings(
        WAGTAILSEARCH_BACKENDS={}
    )
    def test_get_search_backends_with_no_default_defined(self):
        backends = list(get_search_backends())

        self.assertEqual(len(backends), 1)
        self.assertIsInstance(backends[0], DatabaseSearchBackend)

    @override_settings(
        WAGTAILSEARCH_BACKENDS={
            'default': {
                'BACKEND': 'wagtail.search.backends.db'
            },
            'another-backend': {
                'BACKEND': 'wagtail.search.backends.db'
            },
        }
    )
    def test_get_search_backends_multiple(self):
        backends = list(get_search_backends())

        self.assertEqual(len(backends), 2)

    def test_get_search_backends_with_auto_update(self):
        backends = list(get_search_backends(with_auto_update=True))

        # Auto update is the default
        self.assertEqual(len(backends), 1)

    @override_settings(
        WAGTAILSEARCH_BACKENDS={
            'default': {
                'BACKEND': 'wagtail.search.backends.db',
                'AUTO_UPDATE': False,
            },
        }
    )
    def test_get_search_backends_with_auto_update_disabled(self):
        backends = list(get_search_backends(with_auto_update=True))

        self.assertEqual(len(backends), 0)

    @override_settings(
        WAGTAILSEARCH_BACKENDS={
            'default': {
                'BACKEND': 'wagtail.search.backends.db',
                'AUTO_UPDATE': False,
            },
        }
    )
    def test_get_search_backends_without_auto_update_disabled(self):
        backends = list(get_search_backends())

        self.assertEqual(len(backends), 1)
