# coding: utf-8
from __future__ import absolute_import, unicode_literals

from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO

from wagtail.tests.search.models import SearchTest
from wagtail.wagtailsearch.tests.test_backends import BackendTests

from ..utils import BOOSTS_WEIGHTS, WEIGHTS_VALUES, determine_boosts_weights, get_weight


class TestPostgresSearchBackend(BackendTests, TestCase):
    backend_path = 'wagtail.contrib.postgres_search.backend'

    def test_update_index_command(self):
        self.backend.reset_index()

        results = self.backend.search(None, SearchTest)
        # We find results anyway because we searched for nothing.
        self.assertSetEqual(set(results),
                            {self.testa, self.testb, self.testc.searchtest_ptr,
                             self.testd.searchtest_ptr})

        # But now, we can't find anything because the index is empty.
        results = self.backend.search('hello', SearchTest)
        self.assertSetEqual(set(results), set())
        results = self.backend.search('world', SearchTest)
        self.assertSetEqual(set(results), set())

        # Run update_index command
        with self.ignore_deprecation_warnings():
            # ignore any DeprecationWarnings thrown by models with old-style
            # indexed_fields definitions
            call_command('update_index', backend_name=self.backend_name,
                         interactive=False, stdout=StringIO())

        # And now we can finally find results.
        results = self.backend.search('hello', SearchTest)
        self.assertSetEqual(set(results), {self.testa, self.testb,
                                           self.testc.searchtest_ptr})
        results = self.backend.search('world', SearchTest)
        self.assertSetEqual(set(results), {self.testa,
                                           self.testd.searchtest_ptr})

    def test_weights(self):
        self.assertListEqual(BOOSTS_WEIGHTS,
                             [(10, 'A'), (2, 'B'), (0, 'C'), (0, 'D')])
        self.assertListEqual(WEIGHTS_VALUES, [0, 0, 0.2, 1.0])

        self.assertEqual(get_weight(15), 'A')
        self.assertEqual(get_weight(10), 'A')
        self.assertEqual(get_weight(9.9), 'B')
        self.assertEqual(get_weight(2), 'B')
        self.assertEqual(get_weight(1.9), 'C')
        self.assertEqual(get_weight(0), 'C')
        self.assertEqual(get_weight(-1), 'D')

        self.assertListEqual(determine_boosts_weights([1]),
                             [(1, 'A'), (0, 'B'), (0, 'C'), (0, 'D')])
        self.assertListEqual(determine_boosts_weights([-1]),
                             [(-1, 'A'), (-1, 'B'), (-1, 'C'), (-1, 'D')])
        self.assertListEqual(determine_boosts_weights([-1, 1, 2]),
                             [(2, 'A'), (1, 'B'), (-1, 'C'), (-1, 'D')])
        self.assertListEqual(determine_boosts_weights([0, 1, 2, 3]),
                             [(3, 'A'), (2, 'B'), (1, 'C'), (0, 'D')])
        self.assertListEqual(determine_boosts_weights([0, 0.25, 0.75, 1, 1.5]),
                             [(1.5, 'A'), (1, 'B'), (0.5, 'C'), (0, 'D')])
        self.assertListEqual(determine_boosts_weights([0, 1, 2, 3, 4, 5, 6]),
                             [(6, 'A'), (4, 'B'), (2, 'C'), (0, 'D')])
        self.assertListEqual(determine_boosts_weights([-2, -1, 0, 1, 2, 3, 4]),
                             [(4, 'A'), (2, 'B'), (0, 'C'), (-2, 'D')])

    def test_ranking(self):
        title_search_field = SearchTest.search_fields[0]
        original_title_boost = title_search_field.boost
        title_search_field.boost = 2

        SearchTest.objects.all().delete()

        vivaldi_composer = SearchTest.objects.create(
            title='Antonio Vivaldi',
            content='Born in 1678, Vivaldi is one of Earth’s '
                    'most inspired composers. '
                    'Read more about it in your favorite browser.')
        vivaldi_browser = SearchTest.objects.create(
            title='The Vivaldi browser',
            content='This web browser is based on WebKit.')

        results = self.backend.search('vivaldi', SearchTest)
        self.assertListEqual(list(results),
                             [vivaldi_composer, vivaldi_browser])
        results = self.backend.search('browser', SearchTest)
        self.assertListEqual(list(results),
                             [vivaldi_browser, vivaldi_composer])

        title_search_field.boost = original_title_boost
