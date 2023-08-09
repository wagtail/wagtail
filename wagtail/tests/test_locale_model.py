from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from wagtail.models import Locale, Page
from wagtail.test.i18n.models import TestPage


def make_test_page(**kwargs):
    root_page = Page.objects.get(id=1)
    kwargs.setdefault("title", "Test page")
    return root_page.add_child(instance=TestPage(**kwargs))


class TestLocaleModel(TestCase):
    def setUp(self):
        language_codes = dict(settings.LANGUAGES).keys()

        for language_code in language_codes:
            Locale.objects.get_or_create(language_code=language_code)

    def test_default(self):
        locale = Locale.get_default()
        self.assertEqual(locale.language_code, "en")

    @override_settings(LANGUAGE_CODE="fr-ca")
    def test_default_doesnt_have_to_be_english(self):
        locale = Locale.get_default()
        self.assertEqual(locale.language_code, "fr")

    def test_get_active_default(self):
        self.assertEqual(Locale.get_active().language_code, "en")

    def test_get_active_overridden(self):
        with translation.override("fr"):
            self.assertEqual(Locale.get_active().language_code, "fr")

    def test_language_name(self):
        for language_code, expected_result in (
            ("en", "English"),
            ("fr", "French"),
            ("zh-hans", "Simplified Chinese"),
        ):
            with self.subTest(language_code):
                locale = Locale(language_code=language_code)
                self.assertEqual(locale.language_name, expected_result)

    def test_language_name_for_unrecognised_language(self):
        locale = Locale(language_code="foo")
        with self.assertRaises(KeyError):
            locale.language_name

    def test_language_name_local(self):
        for language_code, expected_result in (
            ("en", "English"),
            ("fr", "français"),
            ("zh-hans", "简体中文"),
        ):
            with self.subTest(language_code):
                locale = Locale(language_code=language_code)
                self.assertEqual(locale.language_name_local, expected_result)

    def test_language_name_local_for_unrecognised_language(self):
        locale = Locale(language_code="foo")
        with self.assertRaises(KeyError):
            locale.language_name_local

    def test_language_name_localized_reflects_active_language(self):
        for language_code in (
            "fr",  # French
            "zh-hans",  # Simplified Chinese
            "ca",  # Catalan
            "de",  # German
        ):
            with self.subTest(language_code):
                locale = Locale(language_code=language_code)
                with translation.override("en"):
                    self.assertEqual(
                        locale.language_name_localized, locale.language_name
                    )
                with translation.override(language_code):
                    # NB: Casing can differ between these, hence the lower()
                    self.assertEqual(
                        locale.language_name_localized.lower(),
                        locale.language_name_local.lower(),
                    )

    def test_language_name_localized_for_unconfigured_language(self):
        locale = Locale(language_code="zh-hans")
        self.assertEqual(locale.language_name_localized, "Simplified Chinese")
        with translation.override("zh-hans"):
            self.assertEqual(locale.language_name_localized, locale.language_name_local)

    def test_language_name_localized_for_unrecognised_language(self):
        locale = Locale(language_code="foo")
        with self.assertRaises(KeyError):
            locale.language_name_localized

    def test_is_bidi(self):
        for language_code, expected_result in (
            ("en", False),
            ("ar", True),
            ("he", True),
            ("fr", False),
            ("foo", False),
        ):
            with self.subTest(language_code):
                locale = Locale(language_code=language_code)
                self.assertIs(locale.is_bidi, expected_result)

    def test_is_default(self):
        for language_code, expected_result in (
            (settings.LANGUAGE_CODE, True),  # default
            ("zh-hans", False),  # alternative
            ("foo", False),  # invalid
        ):
            with self.subTest(language_code):
                locale = Locale(language_code=language_code)
                self.assertIs(locale.is_default, expected_result)

    def test_is_active(self):
        for locale_language, active_language, expected_result in (
            (settings.LANGUAGE_CODE, settings.LANGUAGE_CODE, True),
            (settings.LANGUAGE_CODE, "fr", False),
            ("zh-hans", settings.LANGUAGE_CODE, False),
            ("en", "en-gb", True),
            ("foo", settings.LANGUAGE_CODE, False),
        ):
            with self.subTest(f"locale={locale_language} active={active_language}"):
                with translation.override(active_language):
                    locale = Locale(language_code=locale_language)
                    self.assertEqual(locale.is_active, expected_result)

    def test_get_display_name(self):
        for language_code, expected_result in (
            ("en", "English"),  # configured
            ("zh-hans", "Simplified Chinese"),  # not configured but valid
            ("foo", "foo"),  # not configured or valid
        ):
            locale = Locale(language_code=language_code)
            with self.subTest(language_code):
                self.assertEqual(locale.get_display_name(), expected_result)

    def test_str_reflects_get_display(self):
        for language_code in ("en", "zh-hans", "foo"):
            locale = Locale(language_code=language_code)
            with self.subTest(language_code):
                self.assertEqual(str(locale), locale.get_display_name())

    @override_settings(LANGUAGES=[("en", _("English")), ("fr", _("French"))])
    def test_str_when_languages_uses_gettext(self):
        locale = Locale(language_code="en")
        self.assertIsInstance(locale.__str__(), str)

    @override_settings(LANGUAGE_CODE="fr")
    def test_change_root_page_locale_on_locale_deletion(self):
        """
        On deleting the locale used for the root page (but no 'real' pages), the
        root page should be reassigned to a new locale (the default one, if possible)
        """
        # change 'real' pages first
        Page.objects.filter(depth__gt=1).update(
            locale=Locale.objects.get(language_code="fr")
        )
        self.assertEqual(Page.get_first_root_node().locale.language_code, "en")
        Locale.objects.get(language_code="en").delete()
        self.assertEqual(Page.get_first_root_node().locale.language_code, "fr")
