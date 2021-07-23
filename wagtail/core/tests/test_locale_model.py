from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from wagtail.core.models import Locale, Page
from wagtail.tests.i18n.models import TestPage


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

    def test_get_display_name(self):
        locale = Locale.objects.get(language_code="en")
        self.assertEqual(locale.get_display_name(), "English")

    def test_get_display_name_for_unconfigured_langauge(self):
        # This language is not in LANGUAGES so it should just return the language code
        locale = Locale.objects.create(language_code="foo")
        self.assertIsNone(locale.get_display_name())

    def test_str(self):
        locale = Locale.objects.get(language_code="en")
        self.assertEqual(str(locale), "English")

    def test_str_for_unconfigured_langauge(self):
        # This language is not in LANGUAGES so it should just return the language code
        locale = Locale.objects.create(language_code="foo")
        self.assertEqual(str(locale), "foo")

    @override_settings(LANGUAGES=[("en", _("English")), ("fr", _("French"))])
    def test_str_when_languages_uses_gettext(self):
        locale = Locale.objects.get(language_code="en")
        self.assertIsInstance(locale.__str__(), str)

    @override_settings(LANGUAGE_CODE="fr")
    def test_change_root_page_locale_on_locale_deletion(self):
        """
        On deleting the locale used for the root page (but no 'real' pages), the
        root page should be reassigned to a new locale (the default one, if possible)
        """
        # change 'real' pages first
        Page.objects.filter(depth__gt=1).update(locale=Locale.objects.get(language_code="fr"))
        self.assertEqual(Page.get_first_root_node().locale.language_code, "en")
        Locale.objects.get(language_code="en").delete()
        self.assertEqual(Page.get_first_root_node().locale.language_code, "fr")
