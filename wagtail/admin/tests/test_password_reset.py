import unittest

from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.test.utils import WagtailTestUtils


class TestUserPasswordReset(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    # need to clear urlresolver caches before/after tests, because we override ROOT_URLCONF
    # in some tests here
    def setUp(self):
        from django.urls import clear_url_caches

        clear_url_caches()

    def tearDown(self):
        from django.urls import clear_url_caches

        clear_url_caches()

    def test_login_has_password_reset_option(self):
        response = self.client.get(reverse("wagtailadmin_login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Forgotten password?")

    @override_settings(WAGTAIL_PASSWORD_RESET_ENABLED=False)
    def test_login_has_no_password_reset_option_when_disabled(self):
        response = self.client.get(reverse("wagtailadmin_login"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Forgotten password?")

    @override_settings(WAGTAIL_PASSWORD_RESET_ENABLED=False)
    def test_password_reset_view_disabled(self):
        """
        This tests that the password reset view responds with a 404
        when setting WAGTAIL_PASSWORD_RESET_ENABLED is False
        """
        # Get password reset page
        response = self.client.get(reverse("wagtailadmin_password_reset"))

        # Check that the user received a 404
        self.assertEqual(response.status_code, 404)

    @override_settings(ROOT_URLCONF="wagtail.admin.urls")
    def test_email_found_default_url(self):
        response = self.client.post(
            reverse("wagtailadmin_password_reset"), {"email": "siteeditor@example.com"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("testserver", mail.outbox[0].body)

    @override_settings(
        ROOT_URLCONF="wagtail.admin.urls", WAGTAILADMIN_BASE_URL="http://mysite.com"
    )
    def test_email_found_base_url(self):
        response = self.client.post(
            reverse("wagtailadmin_password_reset"), {"email": "siteeditor@example.com"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("mysite.com", mail.outbox[0].body)

    @unittest.skipUnless(
        settings.AUTH_USER_MODEL == "customuser.CustomUser",
        "only applicable to CustomUser",
    )
    def test_password_reset_email_contains_username(self):
        self.client.post(
            reverse("wagtailadmin_password_reset"), {"email": "siteeditor@example.com"}
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(
            "Your username (in case you've forgotten): siteeditor", mail.outbox[0].body
        )

    @unittest.skipUnless(
        settings.AUTH_USER_MODEL == "emailuser.EmailUser",
        "only applicable to EmailUser",
    )
    def test_password_reset_no_username_when_email_is_username(self):
        # When the user model is using email as the username, the password reset email
        # should not contain "Your username (in case you've forgotten)..."
        self.client.post(
            reverse("wagtailadmin_password_reset"), {"email": "siteeditor@example.com"}
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn(
            "Your username (in case you've forgotten)", mail.outbox[0].body
        )
