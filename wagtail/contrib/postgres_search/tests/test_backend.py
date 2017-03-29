from __future__ import absolute_import, unicode_literals

from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO

from wagtail.tests.search.models import SearchTest
from wagtail.wagtailsearch.tests.test_backends import BackendTests


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
