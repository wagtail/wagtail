from django.test import RequestFactory, TestCase, override_settings

from wagtail import __version__
from wagtail.admin.views.home import UpgradeNotificationPanel
from wagtail.test.utils import WagtailTestUtils
from wagtail.users.models import UserProfile


class TestUpgradeNotificationPanel(WagtailTestUtils, TestCase):
    ATTR_UPGRADE_CHECK_LTS = "data-w-upgrade-lts-only-value"
    ATTR_CURRENT_VERSION = "data-w-upgrade-current-version-value"
    ATTR_DISMISSIBLE_ID = "data-w-dismissible-id-value"
    ATTR_LAST_DISMISSED_VALUE = "data-w-dismissible-value-param"
    DISMISSIBLE_ID = "last_upgrade_check"

    @classmethod
    def setUpTestData(cls):
        cls.panel = UpgradeNotificationPanel()
        cls.request_factory = RequestFactory()
        cls.user = cls.create_user(username="tester")
        cls.superuser = cls.create_superuser(username="supertester")
        cls.request = cls.request_factory.get("/")

    def test_get_upgrade_check_setting_default(self):
        self.assertTrue(self.panel.get_upgrade_check_setting())

    @override_settings(WAGTAIL_ENABLE_UPDATE_CHECK=False)
    def test_get_upgrade_check_setting_false(self):
        self.assertFalse(self.panel.get_upgrade_check_setting())

    @override_settings(WAGTAIL_ENABLE_UPDATE_CHECK="LTS")
    def test_get_upgrade_check_setting_LTS(self):
        self.assertEqual(self.panel.get_upgrade_check_setting(), "LTS")

    @override_settings(WAGTAIL_ENABLE_UPDATE_CHECK="lts")
    def test_get_upgrade_check_setting_lts(self):
        self.assertEqual(self.panel.get_upgrade_check_setting(), "lts")

    def test_upgrade_check_lts_only_default(self):
        self.assertFalse(self.panel.upgrade_check_lts_only())

    @override_settings(WAGTAIL_ENABLE_UPDATE_CHECK=False)
    def test_upgrade_check_lts_only_setting_true(self):
        self.assertFalse(self.panel.upgrade_check_lts_only())

    @override_settings(WAGTAIL_ENABLE_UPDATE_CHECK="LTS")
    def test_upgrade_check_lts_only_setting_LTS(self):
        self.assertTrue(self.panel.upgrade_check_lts_only())

    @override_settings(WAGTAIL_ENABLE_UPDATE_CHECK="lts")
    def test_upgrade_check_lts_only_setting_lts(self):
        self.assertTrue(self.panel.upgrade_check_lts_only())

    def test_render_html_normal_user(self):
        self.request.user = self.user
        parent_context = {"request": self.request}

        result = self.panel.render_html(parent_context)

        self.assertEqual(result, "")

    def test_render_html_superuser(self):
        self.request.user = self.superuser
        parent_context = {"request": self.request}

        result = self.panel.render_html(parent_context)
        soup = self.get_soup(result)
        controller = soup.select_one("[data-controller]")
        self.assertIsNotNone(controller)
        self.assertEqual(
            set(controller["data-controller"].split()),
            {"w-upgrade", "w-dismissible"},
        )
        self.assertFalse(controller.get(self.ATTR_UPGRADE_CHECK_LTS))
        self.assertEqual(
            controller.get(self.ATTR_DISMISSIBLE_ID),
            self.DISMISSIBLE_ID,
        )
        toggle = soup.select_one("[data-action='w-dismissible#toggle']")
        self.assertIsNotNone(toggle)
        self.assertEqual(toggle.get("aria-label"), "Close")
        self.assertIsNone(toggle.get(self.ATTR_LAST_DISMISSED_VALUE))

    @override_settings(WAGTAIL_ENABLE_UPDATE_CHECK=False)
    def test_render_html_setting_false(self):
        self.request.user = self.superuser
        parent_context = {"request": self.request}

        result = self.panel.render_html(parent_context)

        self.assertEqual(result, "")

    def test_render_html_setting_lts(self):
        self.request.user = self.superuser
        parent_context = {"request": self.request}
        setting_values = ["lts", "LTS"]
        for value in setting_values:
            with self.subTest(setting=value):
                with override_settings(WAGTAIL_ENABLE_UPDATE_CHECK=value):
                    result = self.panel.render_html(parent_context)

                soup = self.get_soup(result)
                controller = soup.select_one("[data-controller]")
                self.assertIsNotNone(controller)
                self.assertEqual(
                    set(controller["data-controller"].split()),
                    {"w-upgrade", "w-dismissible"},
                )
                self.assertEqual(
                    controller.get(self.ATTR_UPGRADE_CHECK_LTS),
                    "true",
                )
                self.assertEqual(
                    controller.get(self.ATTR_DISMISSIBLE_ID),
                    self.DISMISSIBLE_ID,
                )
                toggle = soup.select_one("[data-action='w-dismissible#toggle']")
                self.assertIsNotNone(toggle)
                self.assertEqual(toggle.get("aria-label"), "Close")
                self.assertIsNone(toggle.get(self.ATTR_LAST_DISMISSED_VALUE))

    def test_render_html_dismissed_version(self):
        profile = UserProfile.get_for_user(self.superuser)
        profile.dismissibles.update({self.DISMISSIBLE_ID: "6.2.2"})
        profile.save()
        self.request.user = self.superuser
        parent_context = {"request": self.request}

        result = self.panel.render_html(parent_context)
        soup = self.get_soup(result)

        controller = soup.select_one("[data-controller='w-upgrade w-dismissible']")
        self.assertIsNotNone(controller)

        self.assertEqual(
            controller.get(self.ATTR_DISMISSIBLE_ID),
            self.DISMISSIBLE_ID,
        )
        self.assertEqual(
            controller.get(self.ATTR_CURRENT_VERSION),
            __version__,
        )
        toggle = soup.select_one("[data-action='w-dismissible#toggle']")
        self.assertIsNotNone(toggle)
        self.assertEqual(toggle.get("aria-label"), "Close")
        self.assertEqual(
            toggle.get(self.ATTR_LAST_DISMISSED_VALUE),
            "6.2.2",
        )
