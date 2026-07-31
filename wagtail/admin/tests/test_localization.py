import zoneinfo
from unittest import mock

from django.test import TestCase

from wagtail.admin import localization


class TestSafeOverrideTimeZone(TestCase):
    def setUp(self):
        localization._WARNED_TIMEZONES.clear()

    def test_falls_back_when_zoneinfo_raises(self):
        with mock.patch.object(
            localization,
            "override_tz",
            side_effect=zoneinfo.ZoneInfoNotFoundError("no tz data"),
        ):
            with self.assertLogs(localization.logger, level="WARNING") as captured:
                with localization._safe_override_tz("Europe/London"):
                    pass

        self.assertEqual(len(captured.output), 1)
        self.assertIn("Europe/London", captured.output[0])
        self.assertIn("tzdata", captured.output[0])

    def test_warning_logged_once_per_timezone(self):
        with mock.patch.object(
            localization,
            "override_tz",
            side_effect=zoneinfo.ZoneInfoNotFoundError("no tz data"),
        ):
            with self.assertLogs(localization.logger, level="WARNING") as captured:
                with localization._safe_override_tz("Europe/London"):
                    pass
                with localization._safe_override_tz("Europe/London"):
                    pass
                with localization._safe_override_tz("Asia/Tokyo"):
                    pass

        self.assertEqual(len(captured.output), 2)
        self.assertIn("Europe/London", captured.output[0])
        self.assertIn("Asia/Tokyo", captured.output[1])

    def test_no_op_when_time_zone_is_none(self):
        with mock.patch.object(localization, "override_tz") as inner:
            with localization._safe_override_tz(None):
                pass
        inner.assert_not_called()

    def test_delegates_to_override_tz_when_available(self):
        with localization._safe_override_tz("UTC"):
            pass
