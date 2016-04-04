# -*- coding: utf-8 -*
from __future__ import absolute_import, unicode_literals

import warnings

from django.test import SimpleTestCase

from wagtail.utils.deprecation import RemovedInWagtail17Warning, SearchFieldsShouldBeAList


class TestThisShouldBeAList(SimpleTestCase):
    def test_add_a_list(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')

            base = SearchFieldsShouldBeAList(['hello'])
            result = base + ['world']

            # Ensure that adding things together works
            self.assertEqual(result, ['hello', 'world'])
            # Ensure that a new SearchFieldsShouldBeAList was returned
            self.assertIsInstance(result, SearchFieldsShouldBeAList)
            # Check that no deprecation warnings were raised
            self.assertEqual(len(w), 0)

    def test_add_a_tuple(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')

            base = SearchFieldsShouldBeAList(['hello'])
            result = base + ('world',)

            # Ensure that adding things together works
            self.assertEqual(result, ['hello', 'world'])
            # Ensure that a new SearchFieldsShouldBeAList was returned
            self.assertIsInstance(result, SearchFieldsShouldBeAList)
            # Check that a deprecation warning was raised
            self.assertEqual(len(w), 1)
            warning = w[0]
            self.assertIs(warning.category, RemovedInWagtail17Warning)
