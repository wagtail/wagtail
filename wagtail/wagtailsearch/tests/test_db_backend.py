from wagtail.tests.utils import unittest

from django.test import TestCase

from .test_backends import BackendTests


class TestDBBackend(BackendTests, TestCase):
    backend_path = 'wagtail.wagtailsearch.backends.db.DBSearch'

    @unittest.expectedFailure
    def test_callable_indexed_field(self):
        super(TestDBBackend, self).test_callable_indexed_field()
