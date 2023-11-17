from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.admin.forms.auth import PasswordResetForm
from wagtail.admin.tests.test_forms import CustomLoginForm, CustomPasswordResetForm
from wagtail.models import Page
from wagtail.test.utils import WagtailTestUtils


class TestLoginView(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.user = self.create_test_user()
        self.homepage = Page.objects.get(url_path="/home/")

    def test_success_redirect(self):
        response = self.client.post(
            reverse("wagtailadmin_login"),
            {
                "username": "test@email.com",
                "password": "password",
            },
        )
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_success_redirect_honour_redirect_get_parameter(self):
        homepage_admin_url = reverse("wagtailadmin_pages:edit", args=[self.homepage.pk])
        login_url = reverse("wagtailadmin_login") + "?next={}".format(
            homepage_admin_url
        )
        response = self.client.post(
            login_url,
            {
                "username": "test@email.com",
                "password": "password",
            },
        )
        self.assertRedirects(response, homepage_admin_url)

    def test_success_redirect_honour_redirect_post_parameter(self):
        homepage_admin_url = reverse("wagtailadmin_pages:edit", args=[self.homepage.pk])
        response = self.client.post(
            reverse("wagtailadmin_login"),
            {
                "username": "test@email.com",
                "password": "password",
                "next": homepage_admin_url,
            },
        )
        self.assertRedirects(response, homepage_admin_url)

    def test_already_authenticated_redirect(self):
        self.login(username="test@email.com", password="password")

        response = self.client.get(reverse("wagtailadmin_login"))
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_already_authenticated_redirect_honour_redirect_get_parameter(self):
        self.login(username="test@email.com", password="password")

        homepage_admin_url = reverse("wagtailadmin_pages:edit", args=[self.homepage.pk])
        login_url = reverse("wagtailadmin_login") + "?next={}".format(
            homepage_admin_url
        )
        response = self.client.get(login_url)
        self.assertRedirects(response, homepage_admin_url)

    @override_settings(LANGUAGE_CODE="de")
    def test_language_code(self):
        response = self.client.get(reverse("wagtailadmin_login"))
        self.assertContains(
            response, '<html lang="de" dir="ltr" class="w-theme-system">'
        )

    @override_settings(LANGUAGE_CODE="he")
    def test_bidi_language_changes_dir_attribute(self):
        response = self.client.get(reverse("wagtailadmin_login"))
        self.assertContains(
            response, '<html lang="he" dir="rtl" class="w-theme-system">'
        )

    @override_settings(
        WAGTAILADMIN_USER_LOGIN_FORM="wagtail.admin.tests.test_forms.CustomLoginForm"
    )
    def test_login_page_renders_extra_fields(self):
        response = self.client.get(reverse("wagtailadmin_login"))
        self.assertContains(
            response,
            """
            <input type="text" name="captcha" required
            aria-describedby="id_captcha-helptext" id="id_captcha">
            """,
            html=True,
        )
        self.assertContains(
            response,
            """
            <div class="w-field__help" id="id_captcha-helptext" data-field-help>
                <div class="help">should be in extra_fields()</div>
            </div>
            """,
            html=True,
        )

    @override_settings(
        WAGTAILADMIN_USER_LOGIN_FORM="wagtail.admin.tests.test_forms.CustomLoginForm"
    )
    def test_login_page_renders_custom_form_non_field_errors(self):
        response = self.client.post(
            reverse("wagtailadmin_login"),
            {
                "username": "test@email.com",
                "password": "password",
                "captcha": "unsolved",
            },
        )
        self.assertContains(response, "Captcha is invalid")

    @override_settings(
        WAGTAILADMIN_USER_LOGIN_FORM="wagtail.admin.tests.test_forms.CustomLoginForm"
    )
    def test_login_page_renders_custom_form_login_error(self):
        response = self.client.post(
            reverse("wagtailadmin_login"),
            {
                "username": "test@email.com",
                "password": "bad-password",
                "captcha": "solved",
            },
        )
        msg = CustomLoginForm.error_messages["invalid_login"] % {
            "username_field": get_user_model().USERNAME_FIELD
        }
        self.assertContains(response, msg, html=True)

    def test_session_expire_on_browser_close(self):
        self.client.post(
            reverse("wagtailadmin_login"),
            {
                "username": "test@email.com",
                "password": "password",
            },
        )
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    @override_settings(SESSION_COOKIE_AGE=7)
    def test_session_expiry_remember(self):
        self.client.post(
            reverse("wagtailadmin_login"),
            {"username": "test@email.com", "password": "password", "remember": True},
        )
        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.assertEqual(self.client.session.get_expiry_age(), 7)

    def test_password_whitespace_not_stripped(self):
        user_model = get_user_model()
        # Create a user
        user_data = {
            user_model.USERNAME_FIELD: "test2@email.com",
            "email": "test2@email.com",
            "password": "  whitespaced_password  ",
        }
        for field in user_model.REQUIRED_FIELDS:
            if field not in user_data:
                user_data[field] = field

        user_model.objects.create_superuser(**user_data)

        response = self.client.post(
            reverse("wagtailadmin_login"),
            {
                "username": "test2@email.com",
                "password": "  whitespaced_password  ",
            },
        )
        self.assertRedirects(response, reverse("wagtailadmin_home"))


class TestPasswordResetView(TestCase):
    def test_password_reset_view_uses_correct_form(self):
        response = self.client.get(reverse("wagtailadmin_password_reset"))
        self.assertIsInstance(response.context.get("form"), PasswordResetForm)

        with override_settings(
            WAGTAILADMIN_USER_PASSWORD_RESET_FORM="wagtail.admin.tests.test_forms.CustomPasswordResetForm"
        ):
            response = self.client.get(reverse("wagtailadmin_password_reset"))
            self.assertIsInstance(response.context.get("form"), CustomPasswordResetForm)

    @override_settings(
        WAGTAILADMIN_USER_PASSWORD_RESET_FORM="wagtail.admin.tests.test_forms.CustomPasswordResetForm"
    )
    def test_password_reset_page_renders_extra_fields(self):
        response = self.client.get(reverse("wagtailadmin_password_reset"))
        self.assertContains(
            response,
            """
            <input type="text" name="captcha" required
            aria-describedby="id_captcha-helptext" id="id_captcha">
            """,
            html=True,
        )
        self.assertContains(
            response,
            """
            <div class="w-field__help" id="id_captcha-helptext" data-field-help>
                <div class="help">should be in extra_fields()</div>
            </div>
            """,
            html=True,
        )


class TestJsi18nView(TestCase):
    def test_jsi18n_does_not_require_login(self):
        response = self.client.get(reverse("wagtailadmin_javascript_catalog"))
        self.assertEqual(response.status_code, 200)
        # get content type header without the "charset" suffix
        content_type = response["content-type"].split(";")[0]
        self.assertEqual(content_type, "text/javascript")
