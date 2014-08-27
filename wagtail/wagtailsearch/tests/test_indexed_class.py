import warnings

from django.test import TestCase

from wagtail.wagtailsearch import index
from wagtail.tests import models
from wagtail.tests.utils import WagtailTestUtils


class TestContentTypeNames(TestCase):
    def test_base_content_type_name(self):
        name = models.SearchTestChild.indexed_get_toplevel_content_type()
        self.assertEqual(name, 'tests_searchtest')

    def test_qualified_content_type_name(self):
        name = models.SearchTestChild.indexed_get_content_type()
        self.assertEqual(name, 'tests_searchtest_tests_searchtestchild')
