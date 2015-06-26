import unittest

from django.test import TestCase

from .test_backends import BackendTests


class TestDBBackend(BackendTests, TestCase):
    backend_path = 'wagtail.wagtailsearch.backends.db'

    @unittest.expectedFailure
    def test_callable_indexed_field(self):
        super(TestDBBackend, self).test_callable_indexed_field()

    @unittest.expectedFailure
    def test_update_index_command(self):
        super(TestDBBackend, self).test_update_index_command()
