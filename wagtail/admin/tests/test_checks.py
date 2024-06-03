from django.core.checks import Error
from django.test import TestCase, override_settings
from django.utils.formats import reset_format_cache

from wagtail.admin.checks import datetime_format_check
from wagtail.test.utils import WagtailTestUtils


class TestDateTimeChecks(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        reset_format_cache()

    def test_datetime_format(self):
        with override_settings(
            WAGTAIL_CONTENT_LANGUAGES=[
                ("en", "English"),
            ],
            LANGUAGES=[
                ("en", "English"),
            ],
            WAGTAIL_DATE_FORMAT="%m/%d/%Y",
            WAGTAIL_TIME_FORMAT="%H:%M",
            USE_L10N=True,
        ):
            errors = datetime_format_check(None)

        self.assertEqual(errors, [])

    def test_datetime_format_with_unsupported_date(self):
        with override_settings(
            WAGTAIL_CONTENT_LANGUAGES=[
                ("en", "English"),
            ],
            LANGUAGES=[
                ("en", "English"),
            ],
            WAGTAIL_DATE_FORMAT="%d.%m.%Y.",
            WAGTAIL_TIME_FORMAT="%H:%M",
            USE_L10N=True,
        ):
            errors = datetime_format_check(None)

        expected_errors = [
            Error(
                "Configuration error",
                hint="'%d.%m.%Y.' must be in DATE_INPUT_FORMATS for language English (en).",
                obj="WAGTAIL_DATE_FORMAT",
                id="wagtailadmin.E003",
            )
        ]
        self.assertEqual(errors, expected_errors)

    def test_datetime_format_with_unsupported_date_not_using_l10n(self):
        """
        Test that the check doesn't raise an error when USE_L10N is False.
        """

        with override_settings(
            WAGTAIL_CONTENT_LANGUAGES=[
                ("en", "English"),
            ],
            LANGUAGES=[
                ("en", "English"),
            ],
            WAGTAIL_DATE_FORMAT="%d.%m.%Y.",
            WAGTAIL_TIME_FORMAT="%H:%M",
            USE_L10N=False,
        ):
            errors = datetime_format_check(None)
        self.assertEqual(errors, [])

    def test_datetime_format_with_unsupported_datetime_and_time(self):
        with override_settings(
            WAGTAIL_CONTENT_LANGUAGES=[
                ("en", "English"),
            ],
            LANGUAGES=[
                ("en", "English"),
            ],
            WAGTAIL_DATETIME_FORMAT="%d.%m.%Y. %H:%M",
            WAGTAIL_TIME_FORMAT="%I:%M %p",
            USE_L10N=True,
        ):
            errors = datetime_format_check(None)

        expected_errors = [
            Error(
                "Configuration error",
                hint="'%d.%m.%Y. %H:%M' must be in DATETIME_INPUT_FORMATS for language English (en).",
                obj="WAGTAIL_DATETIME_FORMAT",
                id="wagtailadmin.E003",
            ),
            Error(
                "Configuration error",
                hint="'%I:%M %p' must be in TIME_INPUT_FORMATS for language English (en).",
                obj="WAGTAIL_TIME_FORMAT",
                id="wagtailadmin.E003",
            ),
        ]
        self.assertEqual(errors, expected_errors)

    def test_datetime_format_with_overriden_format(self):
        with override_settings(
            WAGTAIL_CONTENT_LANGUAGES=[
                ("en", "English"),
            ],
            LANGUAGES=[
                ("en", "English"),
            ],
            WAGTAIL_DATETIME_FORMAT="%d.%m.%Y. %H:%M",
            FORMAT_MODULE_PATH=["wagtail.admin.tests.formats"],
            USE_L10N=True,
        ):
            errors = datetime_format_check(None)

        self.assertEqual(errors, [])

    def test_datetime_format_with_incorrect_overriden_format(self):
        with override_settings(
            WAGTAIL_CONTENT_LANGUAGES=[
                ("en", "English"),
            ],
            LANGUAGES=[
                ("en", "English"),
            ],
            WAGTAIL_DATETIME_FORMAT="%m.%d.%Y. %H:%M",
            FORMAT_MODULE_PATH=["wagtail.admin.tests.formats"],
            USE_L10N=True,
        ):
            errors = datetime_format_check(None)

        expected_errors = [
            Error(
                "Configuration error",
                hint="'%m.%d.%Y. %H:%M' must be in DATETIME_INPUT_FORMATS for language English (en).",
                obj="WAGTAIL_DATETIME_FORMAT",
                id="wagtailadmin.E003",
            ),
        ]
        self.assertEqual(errors, expected_errors)
