"""
Regression tests for issue #13546: InlinePanel with min_num fails validation
when saving unchanged forms with default values.
"""

from django.db import models
from django.test import TestCase
from modelcluster.fields import ParentalKey
from modelcluster.forms import childformset_factory

from wagtail.admin.forms.models import WagtailBaseChildFormSet
from wagtail.models import Orderable, Page


class TestInlinePanelMinNumWithDefaults(TestCase):
    """
    Test that InlinePanel with min_num correctly validates forms with default values.

    Issue #13546: InlinePanel with min_num=1 was failing validation when saving
    an unchanged form that has default values, because Django's has_changed()
    returns False for forms with only default values.
    """

    def test_formset_validates_with_unchanged_defaults(self):
        """
        Test that formset validates successfully when forms have unchanged defaults.

        This is the core regression test for #13546.
        """

        # Define a minimal child model with defaults
        class TestChild(Orderable):
            page = ParentalKey(
                "wagtailcore.Page", related_name="test_children_defaults"
            )
            field_with_default = models.IntegerField(default=50)

            class Meta:
                app_label = "tests"

        # Create formset with min_num=1 validation
        TestChildFormSet = childformset_factory(
            Page,
            TestChild,
            formset=WagtailBaseChildFormSet,
            fields=["field_with_default"],
            extra=0,
            min_num=1,
            validate_min=True,
        )

        # Create a page instance
        page = Page(title="Test", slug="test")

        # Simulate form data with one form containing default value (unchanged)
        formset_data = {
            "test_children_defaults-TOTAL_FORMS": "1",
            "test_children_defaults-INITIAL_FORMS": "0",
            "test_children_defaults-MIN_NUM_FORMS": "1",
            "test_children_defaults-MAX_NUM_FORMS": "1000",
            "test_children_defaults-0-field_with_default": "50",  # Default value
            "test_children_defaults-0-ORDER": "0",
            "test_children_defaults-0-DELETE": "",
        }

        # Create the formset
        formset = TestChildFormSet(
            formset_data, instance=page, prefix="test_children_defaults"
        )

        # Before the fix, this would fail with "Please submit 1 or more forms"
        # After the fix, it should validate successfully
        self.assertTrue(
            formset.is_valid(),
            f"Formset should be valid with unchanged default values. "
            f"Errors: {formset.errors}, Non-form errors: {formset.non_form_errors()}",
        )

    def test_formset_validates_with_changed_values(self):
        """
        Test that formset still validates correctly when values are changed.

        Ensures the fix doesn't break normal form submission.
        """

        class TestChild(Orderable):
            page = ParentalKey("wagtailcore.Page", related_name="test_children_changed")
            field_with_default = models.IntegerField(default=50)

            class Meta:
                app_label = "tests"

        TestChildFormSet = childformset_factory(
            Page,
            TestChild,
            formset=WagtailBaseChildFormSet,
            fields=["field_with_default"],
            extra=0,
            min_num=1,
            validate_min=True,
        )

        page = Page(title="Test", slug="test")

        # Form data with CHANGED value
        formset_data = {
            "test_children_changed-TOTAL_FORMS": "1",
            "test_children_changed-INITIAL_FORMS": "0",
            "test_children_changed-MIN_NUM_FORMS": "1",
            "test_children_changed-MAX_NUM_FORMS": "1000",
            "test_children_changed-0-field_with_default": "100",  # Changed from default 50
            "test_children_changed-0-ORDER": "0",
            "test_children_changed-0-DELETE": "",
        }

        formset = TestChildFormSet(
            formset_data, instance=page, prefix="test_children_changed"
        )

        self.assertTrue(
            formset.is_valid(),
            f"Formset should be valid with changed values. Errors: {formset.errors}",
        )

    def test_formset_fails_validation_when_min_num_not_met(self):
        """
        Test that min_num validation still works when no forms are submitted.

        Ensures the fix doesn't bypass legitimate validation errors.
        """

        class TestChild(Orderable):
            page = ParentalKey("wagtailcore.Page", related_name="test_children_empty")
            field_with_default = models.IntegerField(default=50)

            class Meta:
                app_label = "tests"

        TestChildFormSet = childformset_factory(
            Page,
            TestChild,
            formset=WagtailBaseChildFormSet,
            fields=["field_with_default"],
            extra=0,
            min_num=1,
            validate_min=True,
        )

        page = Page(title="Test", slug="test")

        # Submit with NO forms (truly empty)
        formset_data = {
            "test_children_empty-TOTAL_FORMS": "0",
            "test_children_empty-INITIAL_FORMS": "0",
            "test_children_empty-MIN_NUM_FORMS": "1",
            "test_children_empty-MAX_NUM_FORMS": "1000",
        }

        formset = TestChildFormSet(
            formset_data, instance=page, prefix="test_children_empty"
        )

        # This should FAIL validation (min_num=1 not met)
        self.assertFalse(
            formset.is_valid(),
            "Formset should be invalid when no forms submitted and min_num=1",
        )

        # Check that the error message is present
        self.assertTrue(
            len(formset.non_form_errors()) > 0,
            "Should have non-form errors when min_num not met",
        )
