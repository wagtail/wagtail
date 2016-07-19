from __future__ import absolute_import, unicode_literals

from contextlib import contextmanager

from django.core import checks
from django.test import TestCase

from wagtail.tests.search import models
from wagtail.wagtailsearch import index


@contextmanager
def patch_search_fields(model, new_search_fields):
    """
    A context manager to allow testing of different search_fields configurations
    without permanently changing the models' search_fields.
    """
    old_search_fields = model.search_fields
    model.search_fields = new_search_fields
    yield
    model.search_fields = old_search_fields


class TestContentTypeNames(TestCase):
    def test_base_content_type_name(self):
        name = models.SearchTestChild.indexed_get_toplevel_content_type()
        self.assertEqual(name, 'searchtests_searchtest')

    def test_qualified_content_type_name(self):
        name = models.SearchTestChild.indexed_get_content_type()
        self.assertEqual(name, 'searchtests_searchtest_searchtests_searchtestchild')


class TestSearchFields(TestCase):
    def make_dummy_type(self, search_fields):
        return type(str('DummyType'), (index.Indexed, ), dict(search_fields=search_fields))

    def test_basic(self):
        cls = self.make_dummy_type([
            index.SearchField('test', boost=100, partial_match=False),
            index.FilterField('filter_test'),
        ])

        self.assertEqual(len(cls.get_search_fields()), 2)
        self.assertEqual(len(cls.get_searchable_search_fields()), 1)
        self.assertEqual(len(cls.get_filterable_search_fields()), 1)

    def test_overriding(self):
        # If there are two fields with the same type and name
        # the last one should override all the previous ones. This ensures that the
        # standard convention of:
        #
        #     class SpecificPageType(Page):
        #         search_fields = Page.search_fields + [some_other_definitions]
        #
        # ...causes the definitions in some_other_definitions to override Page.search_fields
        # as intended.
        cls = self.make_dummy_type([
            index.SearchField('test', boost=100, partial_match=False),
            index.SearchField('test', partial_match=True),
        ])

        self.assertEqual(len(cls.get_search_fields()), 1)
        self.assertEqual(len(cls.get_searchable_search_fields()), 1)
        self.assertEqual(len(cls.get_filterable_search_fields()), 0)

        field = cls.get_search_fields()[0]
        self.assertIsInstance(field, index.SearchField)

        # Boost should be reset to the default if it's not specified by the override
        self.assertIsNone(field.boost)

        # Check that the partial match was overridden
        self.assertTrue(field.partial_match)

    def test_different_field_types_dont_override(self):
        # A search and filter field with the same name should be able to coexist
        cls = self.make_dummy_type([
            index.SearchField('test', boost=100, partial_match=False),
            index.FilterField('test'),
        ])

        self.assertEqual(len(cls.get_search_fields()), 2)
        self.assertEqual(len(cls.get_searchable_search_fields()), 1)
        self.assertEqual(len(cls.get_filterable_search_fields()), 1)

    def test_checking_search_fields(self):
        with patch_search_fields(models.SearchTest, models.SearchTest.search_fields + [index.SearchField('foo')]):
            expected_errors = [
                checks.Warning(
                    "SearchTest.search_fields contains field 'foo' but it doesn't exist",
                    obj=models.SearchTest
                )
            ]
            errors = models.SearchTest.check()
            self.assertEqual(errors, expected_errors)
