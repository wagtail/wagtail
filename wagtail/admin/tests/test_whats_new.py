from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from wagtail.admin.views.home import WhatsNewInWagtailVersionPanel
from wagtail.tests.utils import WagtailTestUtils
from wagtail.users.models import UserProfile


class TestWhatsNewInWagtailVersionPanel(TestCase, WagtailTestUtils):
    @classmethod
    def setUpTestData(cls):
        cls.panel = WhatsNewInWagtailVersionPanel()
        cls.dismissible_id = cls.panel.get_dismissible_id()
        cls.request_factory = RequestFactory()
        cls.user = cls.create_user(username="tester")
        cls.profile = UserProfile.get_for_user(cls.user)

    def get_parent_context(self):
        request = self.request_factory.get("/")
        request.user = self.user
        return {"request": request}

    def test_get_whats_new_banner_setting_default(self):
        self.assertTrue(self.panel.get_whats_new_banner_setting())

    @override_settings(WAGTAIL_ENABLE_WHATS_NEW_BANNER=False)
    def test_get_whats_new_banner_setting_false(self):
        self.assertFalse(self.panel.get_whats_new_banner_setting())

    def test_render_html_user_initial(self):
        result = self.panel.render_html(self.get_parent_context())
        self.assertIn(
            f'<section class="w-whats-new w-dismissible" aria-labelledby="whats-new-heading" data-wagtail-dismissible-id="{self.dismissible_id}">',
            result,
        )
        self.assertIn("Things in Wagtail 4 have changed!", result)

    @override_settings(WAGTAIL_ENABLE_WHATS_NEW_BANNER=False)
    def test_render_html_setting_false(self):
        result = self.panel.render_html(self.get_parent_context())
        self.assertEqual(result, "")

    def test_render_html_user_no_profile(self):
        self.profile.delete()
        self.user.refresh_from_db()
        result = self.panel.render_html(self.get_parent_context())
        self.assertIn(
            f'<section class="w-whats-new w-dismissible" aria-labelledby="whats-new-heading" data-wagtail-dismissible-id="{self.dismissible_id}">',
            result,
        )
        self.assertIn("Things in Wagtail 4 have changed!", result)

    def test_render_html_user_dismissed(self):
        self.profile.dismissibles[self.dismissible_id] = True
        self.profile.save(update_fields=["dismissibles"])
        result = self.panel.render_html(self.get_parent_context())
        self.assertEqual(result, "")


class TestWhatsNewOnDashboard(TestCase, WagtailTestUtils):
    """Test 'What's New In Wagtail' banner rendered by `wagtailadmin_home` view"""

    def setUp(self):
        self.user = self.login()
        self.profile = UserProfile.get_for_user(self.user)
        self.dismissible_id = WhatsNewInWagtailVersionPanel().get_dismissible_id()

    def get(self):
        return self.client.get(reverse("wagtailadmin_home"))

    def test_get_enabled_initial(self):
        response = self.get()
        self.assertContains(
            response,
            f'<section class="w-whats-new w-dismissible" aria-labelledby="whats-new-heading" data-wagtail-dismissible-id="{self.dismissible_id}">',
        )
        self.assertContains(response, "Things in Wagtail 4 have changed!")

    @override_settings(WAGTAIL_ENABLE_WHATS_NEW_BANNER=False)
    def test_get_disabled_initial(self):
        response = self.get()
        self.assertNotContains(
            response,
            f'<section class="w-whats-new w-dismissible" aria-labelledby="whats-new-heading" data-wagtail-dismissible-id="{self.dismissible_id}">',
        )
        self.assertNotContains(response, "Things in Wagtail 4 have changed!")

    def test_render_html_user_no_profile(self):
        self.profile.delete()
        self.user.refresh_from_db()
        response = self.get()
        self.assertContains(
            response,
            f'<section class="w-whats-new w-dismissible" aria-labelledby="whats-new-heading" data-wagtail-dismissible-id="{self.dismissible_id}">',
        )
        self.assertContains(response, "Things in Wagtail 4 have changed!")

    def test_get_enabled_dismissed(self):
        self.profile.dismissibles[self.dismissible_id] = True
        self.profile.save(update_fields=["dismissibles"])

        response = self.get()
        self.assertNotContains(
            response,
            f'<section class="w-whats-new w-dismissible" aria-labelledby="whats-new-heading" data-wagtail-dismissible-id="{self.dismissible_id}">',
        )
        self.assertNotContains(response, "Things in Wagtail 4 have changed!")
