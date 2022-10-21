from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.text import capfirst

from wagtail import hooks
from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.panels import FieldPanel, ObjectList, TabbedInterface
from wagtail.contrib.settings.models import BaseTranslatableSiteSetting
from wagtail.contrib.settings.registry import SettingMenuItem
from wagtail.contrib.settings.utils import get_edit_setting_url
from wagtail.contrib.settings.views import get_setting_edit_handler
from wagtail.models import Locale, Page, Site
from wagtail.test.testapp.models import (
    FileTranslatableSiteSetting,
    IconTranslatableSiteSetting,
    PanelTranslatableSiteSettings,
    TabbedTranslatableSiteSettings,
    TestTranslatableSiteSetting,
)
from wagtail.test.utils import WagtailTestUtils

from .base import TranslatableSiteSettingsTestMixin


class TestTranslatableSiteSettingMenu(TestCase, WagtailTestUtils):
    def login_only_admin(self):
        """Log in with a user that only has permission to access the admin"""
        user = self.create_user(username="test", password="password")
        user.user_permissions.add(
            Permission.objects.get_by_natural_key(
                codename="access_admin", app_label="wagtailadmin", model="admin"
            )
        )
        self.login(username="test", password="password")
        return user

    def test_menu_item_in_admin(self):
        self.login()
        response = self.client.get(reverse("wagtailadmin_home"))

        self.assertContains(
            response, capfirst(TestTranslatableSiteSetting._meta.verbose_name)
        )
        self.assertContains(
            response,
            reverse(
                "wagtailsettings:edit", args=("tests", "testtranslatablesitesetting")
            ),
        )

    def test_menu_item_no_permissions(self):
        self.login_only_admin()
        response = self.client.get(reverse("wagtailadmin_home"))

        self.assertNotContains(response, TestTranslatableSiteSetting._meta.verbose_name)
        self.assertNotContains(
            response,
            reverse(
                "wagtailsettings:edit", args=("tests", "testtranslatablesitesetting")
            ),
        )

    def test_menu_item_icon(self):
        menu_item = SettingMenuItem(
            IconTranslatableSiteSetting, icon="tag", classnames="test-class"
        )
        self.assertEqual(menu_item.icon_name, "tag")
        self.assertEqual(menu_item.classnames, "test-class")

    def test_menu_item_icon_fontawesome(self):
        menu_item = SettingMenuItem(
            IconTranslatableSiteSetting, icon="fa-suitcase", classnames="test-class"
        )
        self.assertEqual(menu_item.icon_name, "")
        self.assertEqual(
            set(menu_item.classnames.split(" ")),
            {"icon", "icon-fa-suitcase", "test-class"},
        )


class BaseTestTranslatableSiteSettingView(TestCase, WagtailTestUtils):
    @classmethod
    def setUpTestData(cls):
        cls.en_locale = Locale.get_default()
        cls.fr_locale = Locale.objects.create(language_code="fr")

    def get(self, site_pk=1, setting=TestTranslatableSiteSetting, locale=None):
        url = self.edit_url(setting=setting, site_pk=site_pk, locale=locale)
        return self.client.get(url)

    def post(
        self, site_pk=1, post_data={}, setting=TestTranslatableSiteSetting, locale=None
    ):
        url = self.edit_url(setting=setting, site_pk=site_pk, locale=locale)
        return self.client.post(url, post_data)

    def edit_url(self, setting, site_pk=1, locale=None):
        args = [setting._meta.app_label, setting._meta.model_name, site_pk]
        return get_edit_setting_url(*args, locale=locale)


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestTranslatableSiteSettingCreateView(BaseTestTranslatableSiteSettingView):
    def setUp(self):
        self.user = self.login()

    def test_get_edit(self):
        for i, locale in enumerate([None, self.fr_locale]):
            with self.subTest(locale=locale):
                response = self.get(locale=locale)
                self.assertEqual(response.status_code, 200)

        # Initial instances are created and cache is warmed up,
        # track number of queries.
        for i, locale in enumerate([None, self.fr_locale]):
            with self.subTest(locale=locale):
                with self.assertNumQueries(15):
                    response = self.get(locale=locale)

    def test_edit_invalid(self):
        for i, locale in enumerate([None, self.fr_locale]):
            with self.subTest(locale=locale):
                response = self.post(post_data={"foo": "bar"}, locale=locale)
                self.assertContains(
                    response, "The setting could not be saved due to errors."
                )
                self.assertContains(response, "error-message", count=2)
                self.assertContains(response, "This field is required", count=2)

    def test_edit(self):
        response = self.post(
            post_data={"title": "Edited site title", "email": "test@example.com"}
        )
        self.assertEqual(response.status_code, 302)

        default_site = Site.objects.get(is_default_site=True)
        setting = TestTranslatableSiteSetting.objects.get(site=default_site)
        self.assertEqual(setting.title, "Edited site title")
        self.assertEqual(setting.email, "test@example.com")
        self.assertEqual(setting.locale, self.en_locale)

        url_finder = AdminURLFinder(self.user)
        expected_url = (
            "/admin/settings/tests/testtranslatablesitesetting/%d/" % default_site.pk
        )
        self.assertEqual(url_finder.get_edit_url(setting), expected_url)

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_edit_i18n_disabled(self):
        response = self.post(
            post_data={"title": "Edited site title", "email": "test@example.com"}
        )
        self.assertEqual(response.status_code, 302)

        default_site = Site.objects.get(is_default_site=True)
        setting = TestTranslatableSiteSetting.objects.get(site=default_site)
        self.assertEqual(setting.title, "Edited site title")
        self.assertEqual(setting.email, "test@example.com")
        self.assertEqual(setting.locale, self.en_locale)

        url_finder = AdminURLFinder(self.user)
        expected_url = (
            "/admin/settings/tests/testtranslatablesitesetting/%d/" % default_site.pk
        )
        self.assertEqual(url_finder.get_edit_url(setting), expected_url)

    def test_edit_with_locale(self):
        response = self.post(
            post_data={"title": "Nouveau titre", "email": "test@exemple.com"},
            locale=self.fr_locale,
        )
        self.assertEqual(response.status_code, 302)

        default_site = Site.objects.get(is_default_site=True)
        setting = TestTranslatableSiteSetting.objects.get(
            site=default_site, locale=self.fr_locale
        )
        self.assertEqual(setting.title, "Nouveau titre")
        self.assertEqual(setting.email, "test@exemple.com")
        self.assertEqual(setting.locale, self.fr_locale)

        url_finder = AdminURLFinder(self.user)
        expected_url = (
            "/admin/settings/tests/testtranslatablesitesetting/%d/?locale=fr"
            % default_site.pk
        )
        self.assertEqual(url_finder.get_edit_url(setting), expected_url)

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_edit_with_locale_i18n_disabled(self):
        default_site = Site.objects.get(is_default_site=True)
        response = self.post(
            post_data={"title": "Nouveau titre", "email": "test@exemple.com"},
            locale=self.fr_locale,
        )
        self.assertEqual(response.status_code, 302)

        # A new setting isn't created for other locales.
        # Ensure only one setting instance exists for the default site and the default locale.
        # .get will raise an error if there are multiple instances.
        setting = TestTranslatableSiteSetting.objects.get(site=default_site)
        self.assertEqual(setting.title, "Nouveau titre")
        self.assertEqual(setting.email, "test@exemple.com")
        self.assertEqual(setting.locale, self.en_locale)

        url_finder = AdminURLFinder(self.user)
        # Ensure there is no locale query string.
        expected_url = (
            "/admin/settings/tests/testtranslatablesitesetting/%d/" % default_site.pk
        )
        self.assertEqual(url_finder.get_edit_url(setting), expected_url)

    def test_file_upload_multipart(self):
        response = self.get(setting=FileTranslatableSiteSetting)
        # Ensure the form supports file uploads
        self.assertContains(response, 'enctype="multipart/form-data"')


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestTranslatableSiteSettingEditView(BaseTestTranslatableSiteSettingView):
    def setUp(self):
        default_site = Site.objects.get(is_default_site=True)

        self.test_setting = TestTranslatableSiteSetting()
        self.test_setting.title = "Site title"
        self.test_setting.email = "initial@example.com"
        self.test_setting.site = default_site
        self.test_setting.locale = Locale.get_default()
        self.test_setting.translation_key = (
            BaseTranslatableSiteSetting._get_translation_key(default_site.id)
        )
        self.test_setting.save()
        self.test_setting_fr = self.test_setting.copy_for_translation(self.fr_locale)
        self.test_setting_fr.save()

        self.login()

    def test_get_edit(self):
        for i, locale in enumerate([None, self.fr_locale]):
            with self.subTest(locale=locale):
                response = self.get(locale=locale)
                self.assertEqual(response.status_code, 200)

    def test_edit_invalid(self):
        for i, locale in enumerate([None, self.fr_locale]):
            with self.subTest(locale=locale):
                response = self.post(post_data={"foo": "bar"}, locale=locale)
                self.assertContains(
                    response, "The setting could not be saved due to errors."
                )
                self.assertContains(response, "error-message", count=2)
                self.assertContains(response, "This field is required", count=2)

    def test_edit(self):
        response = self.post(
            post_data={"title": "Edited site title", "email": "test@example.com"}
        )
        self.assertEqual(response.status_code, 302)
        default_site = Site.objects.get(is_default_site=True)
        setting = TestTranslatableSiteSetting.objects.get(
            site=default_site, locale=Locale.get_default()
        )
        self.assertEqual(setting.title, "Edited site title")
        self.assertEqual(setting.email, "test@example.com")

    def test_edit_with_locale(self):
        response = self.post(
            post_data={"title": "Nouveau titre", "email": "test@exemple.com"},
            locale=self.fr_locale,
        )
        self.assertEqual(response.status_code, 302)

        default_site = Site.objects.get(is_default_site=True)
        setting = TestTranslatableSiteSetting.objects.get(
            site=default_site, locale=self.fr_locale
        )
        self.assertEqual(setting.title, "Nouveau titre")
        self.assertEqual(setting.email, "test@exemple.com")

    def test_get_redirect_to_relevant_instance(self):
        url = reverse(
            "wagtailsettings:edit", args=("tests", "testtranslatablesitesetting")
        )
        default_site = Site.objects.get(is_default_site=True)
        locale_query_string = f"?locale={self.fr_locale.language_code}"

        for locale, query_string in [
            (None, ""),
            (self.fr_locale, locale_query_string),
        ]:
            with self.subTest(locale=locale):
                response = self.client.get(url + query_string)
                self.assertRedirects(
                    response,
                    status_code=302,
                    expected_url="%s%s/%s" % (url, default_site.pk, query_string),
                )

    def test_get_redirect_to_relevant_instance_when_no_sites_defined(self):
        Site.objects.all().delete()
        url = reverse(
            "wagtailsettings:edit", args=("tests", "testtranslatablesitesetting")
        )
        locale_query_string = f"?locale={self.fr_locale.language_code}"

        for locale, query_string in [
            (None, ""),
            (self.fr_locale, locale_query_string),
        ]:
            with self.subTest(locale=locale):
                response = self.client.get(url + query_string, follow=True)
                self.assertRedirects(response, status_code=302, expected_url="/admin/")
                messages = [m.message for m in response.context["messages"]]
                self.assertIn(
                    "This setting could not be opened because there is no site defined.",
                    messages[0],
                )


@override_settings(
    ALLOWED_HOSTS=["testserver", "example.com", "noneoftheabove.example.com"]
)
@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestMultiSite(BaseTestTranslatableSiteSettingView):
    def setUp(self):
        self.default_site = Site.objects.get(is_default_site=True)
        self.other_site = Site.objects.create(
            hostname="example.com", root_page=Page.objects.get(pk=2)
        )
        self.login()

    def test_redirect_to_default(self):
        start_url = get_edit_setting_url("tests", "testtranslatablesitesetting")
        dest_url = get_edit_setting_url(
            "tests", "testtranslatablesitesetting", self.default_site.pk
        )
        locale_query_string = f"?locale={self.fr_locale.language_code}"

        for locale, query_string in [(None, ""), (self.fr_locale, locale_query_string)]:
            with self.subTest(locale=locale):
                response = self.client.get(start_url + query_string, follow=True)
                self.assertRedirects(
                    response,
                    dest_url + query_string,
                    status_code=302,
                    fetch_redirect_response=False,
                )

    def test_redirect_to_current(self):
        start_url = get_edit_setting_url("tests", "testtranslatablesitesetting")
        dest_url = get_edit_setting_url(
            "tests", "testtranslatablesitesetting", self.other_site.pk
        )
        locale_query_string = f"?locale={self.fr_locale.language_code}"

        for locale, query_string in [(None, ""), (self.fr_locale, locale_query_string)]:
            with self.subTest(locale=locale):
                response = self.client.get(
                    start_url + query_string,
                    locale=locale,
                    follow=True,
                    HTTP_HOST=self.other_site.hostname,
                )
                self.assertRedirects(
                    response,
                    dest_url + query_string,
                    status_code=302,
                    fetch_redirect_response=False,
                )

    def test_with_no_current_site(self):
        self.default_site.is_default_site = False
        self.default_site.save()

        start_url = get_edit_setting_url("tests", "testtranslatablesitesetting")
        locale_query_string = f"?locale={self.fr_locale.language_code}"

        for locale, query_string in [(None, ""), (self.fr_locale, locale_query_string)]:
            with self.subTest(locale=locale):
                response = self.client.get(
                    start_url + query_string,
                    locale=locale,
                    follow=True,
                    HTTP_HOST="noneoftheabove.example.com",
                )
                self.assertEqual(302, response.redirect_chain[0][1])

    def test_unknown_site(self):
        for locale in [None, self.fr_locale]:
            with self.subTest(locale=locale):
                response = self.get(site_pk=3, locale=locale)
                self.assertEqual(response.status_code, 404)

    def test_edit(self):
        TestTranslatableSiteSetting.objects.create(
            title="default",
            email="default@example.com",
            site=self.default_site,
            translation_key=BaseTranslatableSiteSetting._get_translation_key(
                self.default_site.id
            ),
        )
        TestTranslatableSiteSetting.objects.create(
            title="other",
            email="other@example.com",
            site=self.other_site,
            translation_key=BaseTranslatableSiteSetting._get_translation_key(
                self.other_site.id
            ),
        )
        response = self.post(
            site_pk=self.other_site.pk,
            post_data={"title": "other-new", "email": "other-other@example.com"},
        )
        self.assertEqual(response.status_code, 302)

        # Check that the correct setting was updated
        other_setting = TestTranslatableSiteSetting.for_site(
            self.other_site, locale=Locale.get_default()
        )
        self.assertEqual(other_setting.title, "other-new")
        self.assertEqual(other_setting.email, "other-other@example.com")

        # Check that the other setting was not updated
        default_setting = TestTranslatableSiteSetting.for_site(
            self.default_site, locale=Locale.get_default()
        )
        self.assertEqual(default_setting.title, "default")
        self.assertEqual(default_setting.email, "default@example.com")

    def test_edit_with_locale(self):
        TestTranslatableSiteSetting.objects.create(
            title="Automne",
            email="automne@exemple.com",
            site=self.default_site,
            locale=self.fr_locale,
            translation_key=BaseTranslatableSiteSetting._get_translation_key(
                self.default_site.id
            ),
        )
        TestTranslatableSiteSetting.objects.create(
            title="Hiver",
            email="hiver@exemple.com",
            site=self.other_site,
            locale=self.fr_locale,
            translation_key=BaseTranslatableSiteSetting._get_translation_key(
                self.other_site.id
            ),
        )
        response = self.post(
            site_pk=self.other_site.pk,
            post_data={"title": "Printemps", "email": "printemps@exemple.com"},
            locale=self.fr_locale,
        )
        self.assertEqual(response.status_code, 302)

        # Check that the correct setting was updated
        other_setting = TestTranslatableSiteSetting.for_site(
            self.other_site, locale=self.fr_locale
        )
        self.assertEqual(other_setting.title, "Printemps")
        self.assertEqual(other_setting.email, "printemps@exemple.com")

        # Check that the other setting was not updated
        default_setting = TestTranslatableSiteSetting.for_site(
            self.default_site, locale=self.fr_locale
        )
        self.assertEqual(default_setting.title, "Automne")
        self.assertEqual(default_setting.email, "automne@exemple.com")


class TestAdminPermission(TestCase, WagtailTestUtils):
    def test_registered_permission(self):
        permission = Permission.objects.get_by_natural_key(
            app_label="tests",
            model="testtranslatablesitesetting",
            codename="change_testtranslatablesitesetting",
        )
        for fn in hooks.get_hooks("register_permissions"):
            if permission in fn():
                break
        else:
            self.fail(
                "Change permission for tests.TestTranslatableSiteSetting not registered"
            )


class TestEditHandlers(TestCase):
    def setUp(self):
        get_setting_edit_handler.cache_clear()

    def test_default_model_introspection(self):
        handler = get_setting_edit_handler(TestTranslatableSiteSetting)
        self.assertIsInstance(handler, ObjectList)
        self.assertEqual(len(handler.children), 2)
        first = handler.children[0]
        self.assertIsInstance(first, FieldPanel)
        self.assertEqual(first.field_name, "title")
        second = handler.children[1]
        self.assertIsInstance(second, FieldPanel)
        self.assertEqual(second.field_name, "email")

    def test_with_custom_panels(self):
        handler = get_setting_edit_handler(PanelTranslatableSiteSettings)
        self.assertIsInstance(handler, ObjectList)
        self.assertEqual(len(handler.children), 1)
        first = handler.children[0]
        self.assertIsInstance(first, FieldPanel)
        self.assertEqual(first.field_name, "title")

    def test_with_custom_edit_handler(self):
        handler = get_setting_edit_handler(TabbedTranslatableSiteSettings)
        self.assertIsInstance(handler, TabbedInterface)
        self.assertEqual(len(handler.children), 2)


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestLocaleSelector(
    TranslatableSiteSettingsTestMixin, BaseTestTranslatableSiteSettingView
):
    LOCALE_SELECTOR_HTML = '<a href="javascript:void(0)" aria-label="English" class="c-dropdown__button u-btn-current w-no-underline">'

    def setUp(self):
        base_url = get_edit_setting_url(
            "tests", "testtranslatablesitesetting", self.default_site.pk
        )
        switch_to_french_url = base_url + f"?locale={self.fr_locale.language_code}"
        self.LOCALE_SELECTOR_HTML_FR = f'<a href="{switch_to_french_url}" aria-label="French" class="u-link is-live w-no-underline">'
        self.login()

    def test_locale_selector(self):
        response = self.get()
        self.assertContains(response, self.LOCALE_SELECTOR_HTML)
        self.assertContains(response, self.LOCALE_SELECTOR_HTML_FR)

    def test_locale_selector_without_translation(self):
        self.default_settings_fr.delete()
        response = self.get()
        self.assertContains(response, self.LOCALE_SELECTOR_HTML)
        self.assertContains(response, self.LOCALE_SELECTOR_HTML_FR)

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_locale_selector_not_present_when_i18n_disabled(self):
        response = self.get()
        self.assertNotContains(response, self.LOCALE_SELECTOR_HTML)
        self.assertNotContains(response, self.LOCALE_SELECTOR_HTML_FR)


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestSiteSelector(
    TranslatableSiteSettingsTestMixin, BaseTestTranslatableSiteSettingView
):
    def setUp(self):
        super().setUp()

        other_site_url = get_edit_setting_url(
            "tests", "testtranslatablesitesetting", self.other_site.pk
        )
        other_site_url_fr = other_site_url + f"?locale={self.fr_locale.language_code}"

        self.DEFAULT_SITE_SELECTOR_HTML = f'<a href="javascript:void(0)" aria-label="{self.default_site}" class="c-dropdown__button u-btn-current w-no-underline">'
        self.OTHER_SITE_SELECTOR_HTML = f'<a href="{other_site_url}" aria-label="{self.other_site}" class="u-link is-live w-no-underline">'
        self.OTHER_SITE_SELECTOR_HTML_FR = f'<a href="{other_site_url_fr}" aria-label="{self.other_site}" class="u-link is-live w-no-underline">'

        self.login()

    def test_site_selector(self):
        """Shows site selector with default locale."""
        response = self.get()
        self.assertContains(response, self.DEFAULT_SITE_SELECTOR_HTML)
        self.assertContains(response, self.OTHER_SITE_SELECTOR_HTML)
        self.assertNotContains(response, self.OTHER_SITE_SELECTOR_HTML_FR)

    def test_site_selector_with_different_locale(self):
        """Shows site selector with specified locale."""
        response = self.get(locale=self.fr_locale)
        self.assertContains(response, self.DEFAULT_SITE_SELECTOR_HTML)
        self.assertNotContains(response, self.OTHER_SITE_SELECTOR_HTML)
        self.assertContains(response, self.OTHER_SITE_SELECTOR_HTML_FR)

    def test_site_selector_without_site(self):
        """Site selector isn't shown when there is only one site."""
        self.other_site.delete()
        response = self.get()
        self.assertNotContains(response, self.DEFAULT_SITE_SELECTOR_HTML)
        self.assertNotContains(response, self.OTHER_SITE_SELECTOR_HTML)
        self.assertNotContains(response, self.OTHER_SITE_SELECTOR_HTML_FR)

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_site_selector_when_i18n_disabled(self):
        response = self.get()
        self.assertContains(response, self.DEFAULT_SITE_SELECTOR_HTML)
        self.assertContains(response, self.OTHER_SITE_SELECTOR_HTML)
        self.assertNotContains(response, self.OTHER_SITE_SELECTOR_HTML_FR)

        response = self.get(locale=self.fr_locale)
        self.assertContains(response, self.DEFAULT_SITE_SELECTOR_HTML)
        self.assertContains(response, self.OTHER_SITE_SELECTOR_HTML)
        self.assertNotContains(response, self.OTHER_SITE_SELECTOR_HTML_FR)
