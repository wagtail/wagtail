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


class TestIndexedFieldsBackwardsCompatibility(TestCase, WagtailTestUtils):
    def test_indexed_fields_backwards_compatibility(self):
        # Get search fields
        with self.ignore_deprecation_warnings():
            search_fields = models.SearchTestOldConfig.get_search_fields()

        search_fields_dict = dict(
            ((field.field_name, type(field)), field)
            for field in search_fields
        )

        # Check that the fields were found
        self.assertEqual(len(search_fields_dict), 2)
        self.assertIn(('title', indexed.SearchField), search_fields_dict.keys())
        self.assertIn(('live', indexed.FilterField), search_fields_dict.keys())

        # Check that the title field has the correct settings
        self.assertTrue(search_fields_dict[('title', indexed.SearchField)].partial_match)
        self.assertEqual(search_fields_dict[('title', indexed.SearchField)].boost, 100)

    def test_indexed_fields_backwards_compatibility_list(self):
        # Get search fields
        with self.ignore_deprecation_warnings():
            search_fields = models.SearchTestOldConfigList.get_search_fields()

        search_fields_dict = dict(
            ((field.field_name, type(field)), field)
            for field in search_fields
        )

        # Check that the fields were found
        self.assertEqual(len(search_fields_dict), 2)
        self.assertIn(('title', indexed.SearchField), search_fields_dict.keys())
        self.assertIn(('content', indexed.SearchField), search_fields_dict.keys())
