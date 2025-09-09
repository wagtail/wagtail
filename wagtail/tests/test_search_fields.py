from contextlib import contextmanager

from django.core import checks
from django.test import TestCase

from wagtail.models import Page
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


class TestSearchFields(TestCase):
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
