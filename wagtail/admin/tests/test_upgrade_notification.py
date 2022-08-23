from django.test import RequestFactory, TestCase, override_settings

from wagtail.admin.views.home import UpgradeNotificationPanel
from wagtail.test.utils import WagtailTestUtils


class TestUpgradeNotificationPanel(TestCase, WagtailTestUtils):
    DATA_ATTRIBUTE_UPGRADE_CHECK = "data-w-upgrade"
    DATA_ATTRIBUTE_UPGRADE_CHECK_LTS = "data-w-upgrade-lts-only"

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

        self.assertIn(self.DATA_ATTRIBUTE_UPGRADE_CHECK, result)
        self.assertNotIn(self.DATA_ATTRIBUTE_UPGRADE_CHECK_LTS, result)

    @override_settings(WAGTAIL_ENABLE_UPDATE_CHECK=False)
    def test_render_html_setting_false(self):
        self.request.user = self.superuser
        parent_context = {"request": self.request}

        result = self.panel.render_html(parent_context)

        self.assertEqual(result, "")

    @override_settings(WAGTAIL_ENABLE_UPDATE_CHECK="LTS")
    def test_render_html_setting_LTS(self):
        self.request.user = self.superuser
        parent_context = {"request": self.request}

        result = self.panel.render_html(parent_context)

        self.assertIn(self.DATA_ATTRIBUTE_UPGRADE_CHECK, result)
        self.assertIn(self.DATA_ATTRIBUTE_UPGRADE_CHECK_LTS, result)

    @override_settings(WAGTAIL_ENABLE_UPDATE_CHECK="lts")
    def test_render_html_setting_lts(self):
        self.request.user = self.superuser
        parent_context = {"request": self.request}

        result = self.panel.render_html(parent_context)

        self.assertIn(self.DATA_ATTRIBUTE_UPGRADE_CHECK, result)
        self.assertIn(self.DATA_ATTRIBUTE_UPGRADE_CHECK_LTS, result)
