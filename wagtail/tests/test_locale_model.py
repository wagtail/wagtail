from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from wagtail.models import Locale, LocaleManager, Page
from wagtail.test.i18n.models import TestPage


def make_test_page(**kwargs):
    root_page = Page.objects.get(id=1)
    kwargs.setdefault("title", "Test page")
    return root_page.add_child(instance=TestPage(**kwargs))


class TestLocaleManager(TestCase):
    def setUp(self):
        Locale.objects.clear_cache()

    def tearDown(self):
        Locale.objects.clear_cache()

    def test_get_for_id_cache(self):
        # At this point, a lookup for a Locale should hit the DB
        with self.assertNumQueries(1):
            result = Locale.objects.get_for_id(1)

        # A second hit, though, won't hit the DB
        with self.assertNumQueries(0):
            cached_result = Locale.objects.get_for_id(1)

        self.assertIs(cached_result, result)

    def test_cache_not_shared_between_managers(self):
        with self.assertNumQueries(1):
            Locale.objects.get_for_id(1)
        with self.assertNumQueries(0):
            Locale.objects.get_for_id(1)

        other_manager = LocaleManager()
        other_manager.model = Locale
        with self.assertNumQueries(1):
            other_manager.get_for_id(1)
        with self.assertNumQueries(0):
            other_manager.get_for_id(1)


class TestLocaleModel(TestCase):
    def setUp(self):
        language_codes = dict(settings.LANGUAGES).keys()

        for language_code in language_codes:
            Locale.objects.get_or_create(language_code=language_code)

        Locale.objects.clear_cache()

    def tearDown(self):
        Locale.objects.clear_cache()

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

    def test_get_display_name_for_unconfigured_language(self):
        # This language is not in LANGUAGES so it should just return the language code
        locale = Locale.objects.create(language_code="foo")
        self.assertIsNone(locale.get_display_name())

    def test_str(self):
        locale = Locale.objects.get(language_code="en")
        self.assertEqual(str(locale), "English")

    def test_str_for_unconfigured_language(self):
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
        Page.objects.filter(depth__gt=1).update(
            locale=Locale.objects.get(language_code="fr")
        )
        self.assertEqual(Page.get_first_root_node().locale.language_code, "en")
        Locale.objects.get(language_code="en").delete()
        self.assertEqual(Page.get_first_root_node().locale.language_code, "fr")

    def test_translatablemixin_cached_locale(self):
        page = Page.objects.filter(depth=2).first()

        # there will be a datatabase hit if the locale hasn't been cached yet
        with self.assertNumQueries(1):
            result = page.cached_locale

        # but a second request should hit the cache only
        with self.assertNumQueries(0):
            cached_result = page.cached_locale

        self.assertIs(cached_result, result)

        # if the locale on the object changes for any reason,
        # cached_locale's return value will change to reflect that
        different_locale = Locale.objects.all().exclude(id=page.locale_id).first()
        page.locale = different_locale
        with self.assertNumQueries(0):
            # the first request will have fully populated the cache,
            # so requests for different locales will benefit
            cached_result = page.cached_locale

        self.assertEqual(cached_result, different_locale)
