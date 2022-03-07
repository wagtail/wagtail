from django.core.exceptions import FieldDoesNotExist
from django.test import SimpleTestCase

from wagtail.contrib.forms.models import AbstractEmailForm
from wagtail.core.models import Page, get_page_models
from wagtail.core.mti_utils import (
    NoConcreteSubclassesError,
    get_concrete_subclasses,
    get_concrete_subclasses_with_fields,
    get_concrete_subclass_lookups,
)
from wagtail.tests.testapp.models import (
    EventPage,
    FormPage,
    FormPageWithCustomFormBuilder,
    FormPageWithCustomSubmission,
    FormPageWithCustomSubmissionListView,
    FormPageWithRedirect,
    JadeFormPage,
    MTIBasePage,
    MTIChildPage,
    OneToOnePage,
    PageWithExcludedCopyField,
    PageWithOldStyleRouteMethod,
    SimplePage,
    SingleEventPage,
)


class TestGetConcreteSubclasses(SimpleTestCase):
    """
    Unit tests for ``wagtail.core.mti_utils.get_concrete_subclasses``.
    """

    def test_with_page_class(self):
        self.assertEqual(
            set(get_concrete_subclasses(Page)),
            set(get_page_models()),
        )

    def test_with_page_subclasses(self):
        self.assertEqual(set(get_concrete_subclasses(EventPage)), {EventPage, SingleEventPage})
        self.assertEqual(set(get_concrete_subclasses(MTIBasePage)), {MTIBasePage, MTIChildPage})

    def test_with_abstract_class(self):
        self.assertEqual(
            set(get_concrete_subclasses(AbstractEmailForm)),
            {
                FormPage,
                JadeFormPage,
                FormPageWithRedirect,
                FormPageWithCustomFormBuilder,
                FormPageWithCustomSubmission,
                FormPageWithCustomSubmissionListView,

            },
        )


class TestGetConcreteSubclassesWithFields(SimpleTestCase):
    """
    Unit tests for ``wagtail.core.mti_utils.get_concrete_subclasses_with_fields``.
    """

    def test_single_field_positive_results_for_page(self):
        # When using a field that all subclasses have
        self.assertEqual(
            set(get_concrete_subclasses_with_fields(Page, "live")),
            set(get_page_models()),
        )
        # When using a field that only some subclasses have
        self.assertEqual(
            set(get_concrete_subclasses_with_fields(Page, "content")),
            {SimplePage, PageWithExcludedCopyField, PageWithOldStyleRouteMethod},
        )

    def test_multiple_field_positive_results_for_page(self):
        # When using fields that all subclasses have
        self.assertEqual(
            set(
                get_concrete_subclasses_with_fields(
                    Page, "title", "live", "has_unpublished_changes"
                )
            ),
            set(get_page_models()),
        )
        # When using fields that only some subclasses have
        self.assertEqual(
            set(get_concrete_subclasses_with_fields(Page, "title", "live", "content")),
            {SimplePage, PageWithExcludedCopyField, PageWithOldStyleRouteMethod},
        )

    def test_single_field_positive_results_for_eventpage(self):
        # When using a field that all subclasses have
        self.assertEqual(
            set(get_concrete_subclasses_with_fields(EventPage, "audience")),
            {EventPage, SingleEventPage},
        )
        # When using a field that only some subclasses have
        self.assertEqual(
            set(get_concrete_subclasses_with_fields(EventPage, "excerpt")),
            {SingleEventPage},
        )

    def test_multiple_field_positive_results_for_eventpage(self):
        # When using fields that all subclasses have
        self.assertEqual(
            set(
                get_concrete_subclasses_with_fields(
                    EventPage, "live", "audience", "date_from"
                )
            ),
            {EventPage, SingleEventPage},
        )
        # When using fields that only some subclasses have
        self.assertEqual(
            set(
                get_concrete_subclasses_with_fields(
                    EventPage, "live", "audience", "date_from", "excerpt"
                )
            ),
            {SingleEventPage},
        )

    def test_single_field_positive_results_for_abstract_page_subclass(self):
        # When using a field that all subclasses have
        self.assertEqual(
            set(get_concrete_subclasses_with_fields(AbstractEmailForm, "to_address")),
            {
                FormPage,
                JadeFormPage,
                FormPageWithRedirect,
                FormPageWithCustomFormBuilder,
                FormPageWithCustomSubmission,
                FormPageWithCustomSubmissionListView,
            },
        )
        # When using a field that only some subclasses have
        self.assertEqual(
            set(
                get_concrete_subclasses_with_fields(
                    AbstractEmailForm, "thank_you_redirect_page"
                )
            ),
            {FormPageWithRedirect},
        )

    def test_multiple_field_positive_results_for_abstract_page_subclass(self):
        # When using fields that all subclasses have
        self.assertEqual(
            set(
                get_concrete_subclasses_with_fields(
                    AbstractEmailForm, "live", "to_address", "subject"
                )
            ),
            {
                FormPage,
                JadeFormPage,
                FormPageWithRedirect,
                FormPageWithCustomFormBuilder,
                FormPageWithCustomSubmission,
                FormPageWithCustomSubmissionListView,
            },
        )
        # When using fields that only some subclasses have
        self.assertEqual(
            set(
                get_concrete_subclasses_with_fields(
                    AbstractEmailForm,
                    "live",
                    "to_address",
                    "subject",
                    "thank_you_redirect_page",
                )
            ),
            {FormPageWithRedirect},
        )

    def test_negative_results_for_page(self):
        self.assertFalse(get_concrete_subclasses_with_fields(Page, "absolute_nonsense"))
        self.assertFalse(
            get_concrete_subclasses_with_fields(Page, "live", "absolute_nonsense")
        )

    def test_negative_results_for_eventpage(self):
        self.assertFalse(
            get_concrete_subclasses_with_fields(EventPage, "absolute_nonsense")
        )
        self.assertFalse(
            get_concrete_subclasses_with_fields(
                EventPage, "audience", "absolute_nonsense"
            )
        )

    def test_negative_results_for_abstract_page_subclass(self):
        self.assertFalse(
            get_concrete_subclasses_with_fields(AbstractEmailForm, "absolute_nonsense")
        )
        self.assertFalse(
            get_concrete_subclasses_with_fields(
                AbstractEmailForm, "to_address", "absolute_nonsense"
            )
        )


class TestGetConcreteSubclassLookups(SimpleTestCase):
    """
    Unit tests for ``wagtail.core.mti_utils.get_concrete_subclass_lookups``.
    """
    def test_page_model_without_for_field(self):
        result = get_concrete_subclass_lookups(Page)

        # The following key/value pairs should be present
        for test_key, test_value in (
            (EventPage, "eventpage"),
            (SingleEventPage, "eventpage__singleeventpage"),
            (MTIBasePage, "mtibasepage"),
            (MTIChildPage, "mtibasepage__mtichildpage"),
        ):
            with self.subTest(f"{test_key} should have the value '{test_value}'"):
                self.assertEqual(result[test_key], test_value)

        # OneToOnePage.page_ptr specifies related_name="+",
        # so cannot be 'looked up' from `Page`
        self.assertNotIn(OneToOnePage, result)

    def test_page_model_with_for_field(self):
        # The Page model implements the 'live' field, so no
        # cross-table lookups are required
        self.assertEqual(
            get_concrete_subclass_lookups(Page, for_field="live"),
            {}
        )

        # Both EventPage and SingleEventPage have the 'date_from'
        # field, but the "eventpage" table stores the value for
        # both models
        self.assertEqual(
            get_concrete_subclass_lookups(Page, for_field="date_from"),
            {EventPage: "eventpage"}
        )

        # Only SingleEventPage has an 'excerpt' field, so the
        # "eventpage" lookup is not useful
        self.assertEqual(
            get_concrete_subclass_lookups(Page, for_field="excerpt"),
            {SingleEventPage: "eventpage__singleeventpage"}
        )

    def test_page_subclasses_without_for_field(self):
        self.assertEqual(
            get_concrete_subclass_lookups(EventPage),
            {SingleEventPage: "singleeventpage"}
        )
        self.assertEqual(
            get_concrete_subclass_lookups(MTIBasePage),
            {MTIChildPage: "mtichildpage"}
        )

    def test_page_subclasses_with_for_field(self):
        self.assertEqual(
            get_concrete_subclass_lookups(EventPage, for_field="excerpt"),
            {SingleEventPage: "singleeventpage"},
        )

    def test_raises_noconcretesubclasseserror_if_model_class_has_no_concrete_subclasses(self):
        with self.assertRaises(NoConcreteSubclassesError):
            get_concrete_subclass_lookups(SimplePage)

    def test_raises_fielddoesnotexist_when_no_subclasses_have_field(self):
        with self.assertRaises(FieldDoesNotExist):
            get_concrete_subclass_lookups(Page, for_field="absolute_nonsense")

        with self.assertRaises(FieldDoesNotExist):
            get_concrete_subclass_lookups(EventPage, for_field="absolute_nonsense")

        with self.assertRaises(FieldDoesNotExist):
            get_concrete_subclass_lookups(SimplePage, for_field="absolute_nonsense")
