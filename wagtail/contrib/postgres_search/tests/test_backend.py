from django.test import TestCase

from wagtail.search.tests.test_backends import BackendTests

from ..utils import BOOSTS_WEIGHTS, WEIGHTS_VALUES, determine_boosts_weights, get_weight


class TestPostgresSearchBackend(BackendTests, TestCase):
    backend_path = 'wagtail.contrib.postgres_search.backend'

    def test_weights(self):
        self.assertListEqual(BOOSTS_WEIGHTS,
                             [(10, 'A'), (2, 'B'), (0.5, 'C'), (0.25, 'D')])
        self.assertListEqual(WEIGHTS_VALUES, [0.025, 0.05, 0.2, 1.0])

        self.assertEqual(get_weight(15), 'A')
        self.assertEqual(get_weight(10), 'A')
        self.assertEqual(get_weight(9.9), 'B')
        self.assertEqual(get_weight(2), 'B')
        self.assertEqual(get_weight(1.9), 'C')
        self.assertEqual(get_weight(0), 'D')
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
