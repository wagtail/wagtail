from __future__ import absolute_import, unicode_literals

import unittest
import warnings

from django.test import TestCase

from wagtail.utils.deprecation import RemovedInWagtail18Warning

from .test_backends import BackendTests


class TestDBBackend(BackendTests, TestCase):
    backend_path = 'wagtail.wagtailsearch.backends.db'

    @unittest.expectedFailure
    def test_callable_indexed_field(self):
        super(TestDBBackend, self).test_callable_indexed_field()

    @unittest.expectedFailure
    def test_update_index_command(self):
        super(TestDBBackend, self).test_update_index_command()


class TestOldNameDeprecationWarning(TestCase):
    def test_old_name_deprecation(self):
        from wagtail.wagtailsearch.backends.db import DBSearch

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')

            DBSearch({})

        self.assertEqual(len(w), 1)
        self.assertIs(w[0].category, RemovedInWagtail18Warning)
