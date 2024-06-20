from contextlib import contextmanager

from django.core import checks
from django.test import TestCase

from wagtail.models import Page
from wagtail.search import index
from wagtail.test.search import models
from wagtail.test.testapp.models import (
    TaggedChildPage,
    TaggedGrandchildPage,
    TaggedPage,
)


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
        name = models.Novel.indexed_get_toplevel_content_type()
        self.assertEqual(name, "searchtests_book")

    def test_qualified_content_type_name(self):
        name = models.Novel.indexed_get_content_type()
        self.assertEqual(name, "searchtests_book_searchtests_novel")


class TestSearchFields(TestCase):
    def make_dummy_type(self, search_fields):
        return type("DummyType", (index.Indexed,), {"search_fields": search_fields})

    def get_checks_result(warning_id=None):
        """Run Django checks on any with the 'search' tag used when registering the check"""
        checks_result = checks.run_checks()
        if warning_id:
            return [warning for warning in checks_result if warning.id == warning_id]
        return checks_result

    def test_basic(self):
        cls = self.make_dummy_type(
            [
                index.SearchField("test", boost=100),
                index.FilterField("filter_test"),
            ]
        )

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
        cls = self.make_dummy_type(
            [
                index.SearchField("test", boost=100),
                index.SearchField("test"),
            ]
        )

        self.assertEqual(len(cls.get_search_fields()), 1)
        self.assertEqual(len(cls.get_searchable_search_fields()), 1)
        self.assertEqual(len(cls.get_filterable_search_fields()), 0)

        field = cls.get_search_fields()[0]
        self.assertIsInstance(field, index.SearchField)

        # Boost should be reset to the default if it's not specified by the override
        self.assertIsNone(field.boost)

    def test_different_field_types_dont_override(self):
        # A search and filter field with the same name should be able to coexist
        cls = self.make_dummy_type(
            [
                index.SearchField("test", boost=100),
                index.FilterField("test"),
            ]
        )

        self.assertEqual(len(cls.get_search_fields()), 2)
        self.assertEqual(len(cls.get_searchable_search_fields()), 1)
        self.assertEqual(len(cls.get_filterable_search_fields()), 1)

    def test_checking_search_fields(self):
        with patch_search_fields(
            models.Book, models.Book.search_fields + [index.SearchField("foo")]
        ):
            expected_errors = [
                checks.Warning(
                    "Book.search_fields contains non-existent field 'foo'",
                    obj=models.Book,
                    id="wagtailsearch.W004",
                )
            ]
            errors = models.Book.check()
            self.assertEqual(errors, expected_errors)

    def test_checking_core_page_fields_are_indexed(self):
        """Run checks to ensure that when core page fields are missing we get a warning"""

        # first confirm that errors show as TaggedPage (in test models) has no Page.search_fields
        errors = [
            error for error in checks.run_checks() if error.id == "wagtailsearch.W001"
        ]

        # should only ever get this warning on the sub-classes of the page model
        self.assertEqual(
            [TaggedPage, TaggedChildPage, TaggedGrandchildPage],
            [error.obj for error in errors],
        )

        for error in errors:
            self.assertEqual(
                error.msg,
                "Core Page fields missing in `search_fields`",
            )
            self.assertIn(
                "Page model search fields `search_fields = Page.search_fields + [...]`",
                error.hint,
            )

        # second check that we get no errors when setting up the models correctly
        with patch_search_fields(
            TaggedPage, Page.search_fields + TaggedPage.search_fields
        ):
            errors = [
                error
                for error in checks.run_checks()
                if error.id == "wagtailsearch.W001"
            ]
            self.assertEqual([], errors)

        # third check that we get no errors when disabling all model search
        with patch_search_fields(TaggedPage, []):
            errors = [
                error
                for error in checks.run_checks()
                if error.id == "wagtailsearch.W001"
            ]
            self.assertEqual([], errors)


class SearchableContentTest(TestCase):
    def setUp(self):
        # Initialize SearchableContent object for testing
        self.searchable_content = index.SearchableContent()

    def test_add_content(self):
        # Test adding content with a specific boost value
        self.searchable_content.add_content(2.0, "first heading")
        self.searchable_content.add_content(1.0, "first paragraph")

        # Check if content is added correctly
        self.assertEqual(self.searchable_content.as_dict(), {2.0: ["first heading"], 1.0: ["first paragraph"]})

    def test_merge_content(self):
        # Test merging content from another SearchableContent object
        other_content = index.SearchableContent({1.5: ["merged paragraph"]})
        self.searchable_content.merge_content(other_content)

        # Check if content is merged correctly
        self.assertEqual(self.searchable_content.as_dict(), {1.5: ["merged paragraph"]})

    def test_multiply_boosts(self):
        # Test multiplying boost values by a given multiplier
        self.searchable_content.add_content(1.0, "first paragraph")
        self.searchable_content.multiply_boosts(2)

        # Check if boosts are multiplied correctly
        self.assertEqual(self.searchable_content.get_unique_boosts(), {2.0})

    def test_get_unique_boosts(self):
        # Test getting unique boost values
        self.searchable_content.add_content(2.0, "first heading")
        self.searchable_content.add_content(1.0, "first paragraph")
        self.searchable_content.add_content(2.0, "second heading")

        # Check if unique boosts are obtained correctly
        self.assertEqual(self.searchable_content.get_unique_boosts(), {1.0, 2.0})

    def test_as_dict(self):
        # Test getting content as a dictionary
        self.searchable_content.add_content(2.0, "first heading")
        self.searchable_content.add_content(1.0, "first paragraph")

        # Check if content is obtained as a dictionary correctly
        self.assertEqual(self.searchable_content.as_dict(), {2.0: ["first heading"], 1.0: ["first paragraph"]})

    def test_as_list(self):
        # Test getting content as a single list
        self.searchable_content.add_content(2.0, "first heading")
        self.searchable_content.add_content(1.0, "first paragraph")

        # Check if content is obtained as a list correctly
        self.assertEqual(self.searchable_content.as_list(), ["first heading", "first paragraph"])
