from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.text import capfirst

from wagtail import hooks
from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.panels import FieldPanel, ObjectList, TabbedInterface
from wagtail.contrib.settings.registry import SettingMenuItem
from wagtail.contrib.settings.utils import get_edit_setting_url
from wagtail.contrib.settings.views import get_setting_edit_handler
from wagtail.models import Locale
from wagtail.test.testapp.models import (
    FileTranslatableGenericSetting,
    IconTranslatableGenericSetting,
    PanelTranslatableGenericSettings,
    TabbedTranslatableGenericSettings,
    TestTranslatableGenericSetting,
)
from wagtail.test.utils import WagtailTestUtils

from .base import TranslatableGenericSettingsTestMixin


class TestTranslatableGenericSettingMenu(TestCase, WagtailTestUtils):
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
            response, capfirst(TestTranslatableGenericSetting._meta.verbose_name)
        )
        self.assertContains(
            response,
            reverse(
                "wagtailsettings:edit", args=("tests", "testtranslatablegenericsetting")
            ),
        )

    def test_menu_item_no_permissions(self):
        self.login_only_admin()
        response = self.client.get(reverse("wagtailadmin_home"))

        self.assertNotContains(
            response, TestTranslatableGenericSetting._meta.verbose_name
        )
        self.assertNotContains(
            response,
            reverse(
                "wagtailsettings:edit", args=("tests", "testtranslatablegenericsetting")
            ),
        )

    def test_menu_item_icon(self):
        menu_item = SettingMenuItem(
            IconTranslatableGenericSetting, icon="tag", classnames="test-class"
        )
        self.assertEqual(menu_item.icon_name, "tag")
        self.assertEqual(menu_item.classnames, "test-class")

    def test_menu_item_icon_fontawesome(self):
        menu_item = SettingMenuItem(
            IconTranslatableGenericSetting, icon="fa-suitcase", classnames="test-class"
        )
        self.assertEqual(menu_item.icon_name, "")
        self.assertEqual(
            set(menu_item.classnames.split(" ")),
            {"icon", "icon-fa-suitcase", "test-class"},
        )


class BaseTestTranslatableGenericSettingView(TestCase, WagtailTestUtils):
    @classmethod
    def setUpTestData(cls):
        cls.en_locale = Locale.get_default()
        cls.fr_locale = Locale.objects.create(language_code="fr")

    def get(self, params={}, setting=TestTranslatableGenericSetting, locale=None):
        url = self.edit_url(setting=setting, locale=locale)
        return self.client.get(url, params)

    def post(self, post_data={}, setting=TestTranslatableGenericSetting, locale=None):
        url = self.edit_url(setting=setting, locale=locale)
        return self.client.post(url, post_data)

    def edit_url(self, setting, locale=None):
        return get_edit_setting_url(
            setting._meta.app_label, setting._meta.model_name, locale=locale
        )


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestTranslatableGenericSettingCreateView(BaseTestTranslatableGenericSettingView):
    def setUp(self):
        self.user = self.login()

    def test_get_edit(self):
        for locale in [None, self.fr_locale]:
            with self.subTest(locale=locale):
                response = self.get(locale=locale)
                self.assertEqual(response.status_code, 200)

    def test_edit_invalid(self):
        for locale in [None, self.fr_locale]:
            with self.subTest(locale=locale):
                response = self.post(post_data={"foo": "bar"})
                self.assertContains(
                    response, "The setting could not be saved due to errors."
                )
                self.assertContains(response, "This field is required", count=2)

    def test_edit(self):
        response = self.post(
            post_data={
                "title": "Edited setting title",
                "email": "edited.email@example.com",
            }
        )
        self.assertEqual(response.status_code, 302)

        setting = TestTranslatableGenericSetting.objects.first()
        self.assertEqual(setting.title, "Edited setting title")
        self.assertEqual(setting.locale, self.en_locale)

        url_finder = AdminURLFinder(self.user)
        expected_url = "/admin/settings/tests/testtranslatablegenericsetting/"
        self.assertEqual(url_finder.get_edit_url(setting), expected_url)

    def test_edit_with_locale(self):
        response = self.post(
            post_data={
                "title": "Nouveau titre",
                "email": "nouveau.email@exemple.com",
            },
            locale=self.fr_locale,
        )
        self.assertEqual(response.status_code, 302)

        setting = TestTranslatableGenericSetting.objects.first()
        self.assertEqual(setting.title, "Nouveau titre")

        url_finder = AdminURLFinder(self.user)
        locale_query_string = f"?locale={self.fr_locale.language_code}"
        expected_url = f"/admin/settings/tests/testtranslatablegenericsetting/{locale_query_string}"
        self.assertEqual(url_finder.get_edit_url(setting), expected_url)

    def test_file_upload_multipart(self):
        response = self.get(setting=FileTranslatableGenericSetting)
        # Ensure the form supports file uploads
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_edit_creates_new_instance_with_default_locale_if_unexisting(self):
        self.assertEqual(TestTranslatableGenericSetting.objects.count(), 0)
        self.client.get(
            get_edit_setting_url(
                TestTranslatableGenericSetting._meta.app_label,
                TestTranslatableGenericSetting._meta.model_name,
            )
        )
        setting = TestTranslatableGenericSetting.objects.get()
        self.assertEqual(setting.locale, self.en_locale)


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestTranslatableGenericSettingEditView(BaseTestTranslatableGenericSettingView):
    def setUp(self):
        self.test_setting = TestTranslatableGenericSetting()
        self.test_setting.title = "Setting title"
        self.test_setting.translation_key = self.test_setting._translation_key
        self.test_setting.save()

        self.test_setting_fr = self.test_setting.copy_for_translation(
            locale=self.fr_locale
        )
        self.test_setting_fr.title = "Titre"
        self.test_setting_fr.save()

        self.login()

    def test_get_edit(self):
        for locale in [None, self.fr_locale]:
            with self.subTest(locale=locale):
                response = self.get(locale=locale)
                self.assertEqual(response.status_code, 200)

    def test_edit_invalid(self):
        for locale in [None, self.fr_locale]:
            with self.subTest(locale=locale):
                response = self.post(post_data={"foo": "bar"}, locale=locale)
                self.assertContains(
                    response, "The setting could not be saved due to errors."
                )
                self.assertContains(response, "This field is required", count=2)

    def test_edit(self):
        response = self.post(
            post_data={
                "title": "Edited setting title",
                "email": "different.email@example.com",
            }
        )
        self.assertEqual(response.status_code, 302)

        setting = TestTranslatableGenericSetting.objects.get(locale=self.en_locale)
        self.assertEqual(setting.title, "Edited setting title")

    def test_edit_with_locale(self):
        response = self.post(
            post_data={
                "title": "Nouveau titre",
                "email": "nouveau.email@exemple.com",
            },
            locale=self.fr_locale,
        )
        self.assertEqual(response.status_code, 302)

        setting = TestTranslatableGenericSetting.objects.get(locale=self.fr_locale)
        self.assertEqual(setting.title, "Nouveau titre")

    def test_for_request(self):
        url = get_edit_setting_url("tests", "testtranslatablegenericsetting")
        locale_query_string = f"?locale={self.fr_locale.language_code}"

        for locale, query_string in [
            (self.en_locale, ""),
            (self.fr_locale, locale_query_string),
        ]:
            with self.subTest(locale=locale):
                response = self.client.get(url + query_string)
                self.assertEqual(response.status_code, 200)


class TestAdminPermission(TestCase, WagtailTestUtils):
    def test_registered_permission(self):
        permission = Permission.objects.get_by_natural_key(
            app_label="tests",
            model="testtranslatablegenericsetting",
            codename="change_testtranslatablegenericsetting",
        )
        for fn in hooks.get_hooks("register_permissions"):
            if permission in fn():
                break
        else:
            self.fail(
                "Change permission for tests.TestTranslatableGenericSetting not registered"
            )


class TestEditHandlers(TestCase):
    def setUp(self):
        get_setting_edit_handler.cache_clear()

    def test_default_model_introspection(self):
        handler = get_setting_edit_handler(TestTranslatableGenericSetting)
        self.assertIsInstance(handler, ObjectList)
        self.assertEqual(len(handler.children), 2)
        first = handler.children[0]
        self.assertIsInstance(first, FieldPanel)
        self.assertEqual(first.field_name, "title")
        second = handler.children[1]
        self.assertIsInstance(second, FieldPanel)
        self.assertEqual(second.field_name, "email")

    def test_with_custom_panels(self):
        handler = get_setting_edit_handler(PanelTranslatableGenericSettings)
        self.assertIsInstance(handler, ObjectList)
        self.assertEqual(len(handler.children), 1)
        first = handler.children[0]
        self.assertIsInstance(first, FieldPanel)
        self.assertEqual(first.field_name, "title")

    def test_with_custom_edit_handler(self):
        handler = get_setting_edit_handler(TabbedTranslatableGenericSettings)
        self.assertIsInstance(handler, TabbedInterface)
        self.assertEqual(len(handler.children), 2)


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestLocaleSelector(
    TranslatableGenericSettingsTestMixin, BaseTestTranslatableGenericSettingView
):
    LOCALE_SELECTOR_HTML = '<a href="javascript:void(0)" aria-label="English" class="c-dropdown__button u-btn-current w-no-underline">'

    def setUp(self):
        base_url = get_edit_setting_url("tests", "testtranslatablegenericsetting")
        locale_query_string = f"?locale={self.fr_locale.language_code}"
        switch_to_french_url = base_url + locale_query_string
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
