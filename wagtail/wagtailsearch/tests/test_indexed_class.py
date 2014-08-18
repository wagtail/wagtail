import warnings

from django.test import TestCase

from wagtail.wagtailsearch import indexed
from wagtail.tests import models
from wagtail.tests.utils import WagtailTestUtils


class TestContentTypeNames(TestCase):
    def test_base_content_type_name(self):
        name = models.SearchTestChild.indexed_get_toplevel_content_type()
        self.assertEqual(name, 'tests_searchtest')

    def test_qualified_content_type_name(self):
        name = models.SearchTestChild.indexed_get_content_type()
        self.assertEqual(name, 'tests_searchtest_tests_searchtestchild')


class TestIndexedFieldsBackwardsIncompatibility(TestCase, WagtailTestUtils):
    def test_use_of_indexed_fields_raises_error(self):
        # SearchTestOldConfig.get_search_fields should raise a RuntimeError
        self.assertRaises(RuntimeError, models.SearchTestOldConfig.get_search_fields)

    def test_use_of_indexed_fields_with_search_fields_doesnt_raise_error(self):
        # SearchTestOldConfigAndNewConfig.get_search_fields shouldnt raise an error
        search_fields = models.SearchTestOldConfigAndNewConfig.get_search_fields()
