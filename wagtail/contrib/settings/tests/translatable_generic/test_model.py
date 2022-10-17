from django.test import TestCase, override_settings

from wagtail.models import Site
from wagtail.test.testapp.models import ImportantPagesTranslatableGenericSetting

from .base import TranslatableGenericSettingsTestMixin


@override_settings(ALLOWED_HOSTS=["localhost", "other"])
@override_settings(WAGTAIL_I18N_ENABLED=True)
class GenericSettingModelTestCase(TranslatableGenericSettingsTestMixin, TestCase):
    def _create_importantpagesgenericsetting_object(self, locale=None):
        return ImportantPagesTranslatableGenericSetting.objects.create(
            sign_up_page=self.default_site.root_page,
            general_terms_page=self.default_site.root_page,
            privacy_policy_page=self.other_site.root_page,
            locale=locale or self.en_locale,
            translation_key=ImportantPagesTranslatableGenericSetting._translation_key,
        )

    def test_request_or_site_with_site_returns_expected_settings(self):
        for locale, expected_settings in [
            (None, self.default_settings),
            (self.fr_locale, self.default_settings_fr),
        ]:
            with self.subTest(locale=locale):
                for site in [None, self.other_site]:
                    with self.subTest(site=site):
                        self.assertEqual(
                            self.model.load(request_or_site=site, locale=locale),
                            expected_settings,
                        )

    def test_request_or_site_with_request_returns_expected_settings(self):
        for locale, expected_settings in [
            (None, self.default_settings),
            (self.fr_locale, self.default_settings_fr),
        ]:
            with self.subTest(locale=locale):
                for site in [None, self.other_site]:
                    with self.subTest(site=site):
                        request = self.get_request(site=site, locale=locale)
                        self.assertEqual(
                            self.model.load(request_or_site=request), expected_settings
                        )

    def test_request_or_site_with_request_result_caching(self):
        # repeat test to show caching is unique per request instance,
        # even when the requests are for the same site and same locale
        for i, request in enumerate(
            [
                self.get_request(locale=self.fr_locale),
                self.get_request(locale=self.fr_locale),
            ],
            1,
        ):
            with self.subTest(attempt=i):
                # force site query beforehand
                Site.find_for_request(request)

                # only the first lookup should result in a query
                # for the locale and the actual instance
                with self.assertNumQueries(2):
                    for i in range(4):
                        self.model.load(request_or_site=request)

    def test_select_related(self, expected_queries=5):
        """The `select_related` attribute on setting models is `None` by default, so fetching foreign keys values requires additional queries"""
        for locale, num_queries in [
            (None, expected_queries),
            (self.fr_locale, expected_queries - 1),
        ]:
            with self.subTest(locale=locale):
                self._create_importantpagesgenericsetting_object(locale=locale)

                # fetch settings and access foreign keys
                with self.assertNumQueries(num_queries):
                    settings = ImportantPagesTranslatableGenericSetting.load(
                        locale=locale
                    )
                    settings.sign_up_page
                    settings.general_terms_page
                    settings.privacy_policy_page

    def test_select_related_use_reduces_total_queries(self):
        """But, `select_related` can be used to reduce the number of queries needed to fetch foreign keys"""
        try:
            # set class attribute temporarily
            ImportantPagesTranslatableGenericSetting.select_related = [
                "sign_up_page",
                "general_terms_page",
                "privacy_policy_page",
            ]
            self.test_select_related(expected_queries=2)
        finally:
            # undo temporary change
            ImportantPagesTranslatableGenericSetting.select_related = None

    def test_get_page_url_returns_page_urls(self):
        for locale in [None, self.fr_locale]:
            with self.subTest(locale=locale):
                self._create_importantpagesgenericsetting_object(locale=locale)

                settings = ImportantPagesTranslatableGenericSetting.load(locale=locale)

                for page_fk_field, expected_result in (
                    ("sign_up_page", "http://localhost/"),
                    ("general_terms_page", "http://localhost/"),
                    ("privacy_policy_page", "http://other/"),
                ):
                    with self.subTest(page_fk_field=page_fk_field):
                        self.assertEqual(
                            settings.get_page_url(page_fk_field), expected_result
                        )

                        self.assertEqual(
                            getattr(settings.page_url, page_fk_field), expected_result
                        )

    def test_get_page_url_raises_attributeerror_if_attribute_name_invalid(self):
        for locale in [None, self.fr_locale]:
            with self.subTest(locale=locale):
                settings = self._create_importantpagesgenericsetting_object(
                    locale=locale
                )
                # when called directly
                with self.assertRaises(AttributeError):
                    settings.get_page_url("not_an_attribute")
                # when called indirectly via shortcut
                with self.assertRaises(AttributeError):
                    settings.page_url.not_an_attribute

    def test_get_page_url_returns_empty_string_if_attribute_value_not_a_page(self):
        for locale in [None, self.fr_locale]:
            with self.subTest(locale=locale):
                settings = self._create_importantpagesgenericsetting_object(
                    locale=locale
                )
                for value in (None, self.default_site):
                    with self.subTest(attribute_value=value):
                        settings.test_attribute = value
                        # when called directly
                        self.assertEqual(settings.get_page_url("test_attribute"), "")
                        # when called indirectly via shortcut
                        self.assertEqual(settings.page_url.test_attribute, "")
