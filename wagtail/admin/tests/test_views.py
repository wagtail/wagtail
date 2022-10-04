from django.contrib.admin.utils import quote
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.admin.forms.auth import PasswordResetForm
from wagtail.admin.tests.test_forms import CustomPasswordResetForm
from wagtail.models import Page
from wagtail.test.utils import WagtailTestUtils


class TestLoginView(TestCase, WagtailTestUtils):
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
        self.assertContains(response, '<html lang="de" dir="ltr">')

    @override_settings(LANGUAGE_CODE="he")
    def test_bidi_language_changes_dir_attribute(self):
        response = self.client.get(reverse("wagtailadmin_login"))
        self.assertContains(response, '<html lang="he" dir="rtl">')

    @override_settings(
        WAGTAILADMIN_USER_LOGIN_FORM="wagtail.admin.tests.test_forms.CustomLoginForm"
    )
    def test_login_page_renders_extra_fields(self):
        response = self.client.get(reverse("wagtailadmin_login"))
        self.assertContains(
            response, '<input type="text" name="captcha" required id="id_captcha">'
        )

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
            response, '<input type="text" name="captcha" required id="id_captcha">'
        )


class TestGenericIndexView(TestCase, WagtailTestUtils):

    fixtures = ["test.json"]

    def get(self, params={}):
        return self.client.get(reverse("testapp_generic_index"), params)

    def test_non_integer_primary_key(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        response_object_count = response.context_data["object_list"].count()
        self.assertEqual(response_object_count, 3)
        self.assertContains(response, "first modelwithstringtypeprimarykey model")
        self.assertContains(response, "second modelwithstringtypeprimarykey model")


class TestGenericEditView(TestCase, WagtailTestUtils):

    fixtures = ["test.json"]

    def get(self, object_pk, params={}):
        return self.client.get(
            reverse("testapp_generic_edit", args=(object_pk,)), params
        )

    def test_non_integer_primary_key(self):
        response = self.get("string-pk-2")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "second modelwithstringtypeprimarykey model")

    def test_non_url_safe_primary_key(self):
        object_pk = 'string-pk-:#?;@&=+$,"[]<>%'
        response = self.get(quote(object_pk))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "non-url-safe pk modelwithstringtypeprimarykey model"
        )

    def test_using_quote_in_edit_url(self):
        object_pk = 'string-pk-:#?;@&=+$,"[]<>%'
        response = self.get(quote(object_pk))
        edit_url = response.context_data["action_url"]
        edit_url_pk = edit_url.split("/")[-2]
        self.assertEqual(edit_url_pk, quote(object_pk))

    def test_using_quote_in_delete_url(self):
        object_pk = 'string-pk-:#?;@&=+$,"[]<>%'
        response = self.get(quote(object_pk))
        delete_url = response.context_data["delete_url"]
        delete_url_pk = delete_url.split("/")[-2]
        self.assertEqual(delete_url_pk, quote(object_pk))


class TestGenericDeleteView(TestCase, WagtailTestUtils):

    fixtures = ["test.json"]

    def get(self, object_pk, params={}):
        return self.client.get(
            reverse("testapp_generic_edit", args=(object_pk,)), params
        )

    def test_with_non_integer_primary_key(self):
        response = self.get("string-pk-2")
        self.assertEqual(response.status_code, 200)

    def test_with_non_url_safe_primary_key(self):
        object_pk = 'string-pk-:#?;@&=+$,"[]<>%'
        response = self.get(quote(object_pk))
        self.assertEqual(response.status_code, 200)
