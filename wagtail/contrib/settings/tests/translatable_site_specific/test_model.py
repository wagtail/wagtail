from django.test import TestCase, override_settings

from wagtail.contrib.settings.models import BaseTranslatableSiteSetting
from wagtail.models import Site
from wagtail.test.testapp.models import (
    ImportantPagesTranslatableSiteSetting,
    TestTranslatableSiteSetting,
)

from .base import TranslatableSiteSettingsTestMixin


@override_settings(ALLOWED_HOSTS=["localhost", "other"])
@override_settings(WAGTAIL_I18N_ENABLED=True)
class TranslatableSettingModelTestCase(TranslatableSiteSettingsTestMixin, TestCase):
    def test_for_site_returns_expected_settings(self):
        for site, locale, expected_settings in (
            (self.default_site, self.en_locale, self.default_settings),
            (self.default_site, self.fr_locale, self.default_settings_fr),
            (self.other_site, self.en_locale, self.other_settings),
            (self.other_site, self.fr_locale, self.other_settings_fr),
        ):
            with self.subTest(site=site):
                self.assertEqual(
                    TestTranslatableSiteSetting.for_site(site, locale=locale),
                    expected_settings,
                )

    def test_for_request_returns_expected_settings(self):
        for request, expected_settings in (
            (self.get_request(), self.default_settings),
            (self.get_request(locale=self.fr_locale), self.default_settings_fr),
            (self.get_request(site=self.other_site), self.other_settings),
            (
                self.get_request(site=self.other_site, locale=self.fr_locale),
                self.other_settings_fr,
            ),
        ):
            with self.subTest(request=request):
                self.assertEqual(
                    TestTranslatableSiteSetting.for_request(request), expected_settings
                )

    def test_for_request_result_caching(self):
        # repeat test to show caching is unique per request instance,
        # even when the requests are for the same site and the same locale
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
                # for the setting and the locale
                with self.assertNumQueries(2):
                    for i in range(4):
                        TestTranslatableSiteSetting.for_request(request)

    def _create_importantpagestranslatablesitesetting_object(self):
        site = self.default_site
        return ImportantPagesTranslatableSiteSetting.objects.create(
            site=site,
            sign_up_page=site.root_page,
            general_terms_page=site.root_page,
            privacy_policy_page=self.other_site.root_page,
            locale=self.fr_locale,
            translation_key=BaseTranslatableSiteSetting._get_translation_key(site.id),
        )

    def test_get_page_url_when_settings_fetched_via_for_request(self):
        self._create_importantpagestranslatablesitesetting_object()

        request = self.get_request(locale=self.fr_locale)
        settings = ImportantPagesTranslatableSiteSetting.for_request(request)

        # Force site root paths query beforehand
        self.default_site.root_page._get_site_root_paths(request)

        for page_fk_field, expected_result in (
            ("sign_up_page", "/"),
            ("general_terms_page", "/"),
            ("privacy_policy_page", "http://other/"),
        ):
            with self.subTest(page_fk_field=page_fk_field):

                with self.assertNumQueries(1):
                    # because results are cached, only the first
                    # request for a URL will trigger 1 query to fetch the page
                    self.assertEqual(
                        settings.get_page_url(page_fk_field), expected_result
                    )

                    # when called directly
                    self.assertEqual(
                        settings.get_page_url(page_fk_field), expected_result
                    )

                    # when called indirectly via shortcut
                    self.assertEqual(
                        getattr(settings.page_url, page_fk_field), expected_result
                    )

    def test_get_page_url_when_for_settings_fetched_via_for_site(self):
        self._create_importantpagestranslatablesitesetting_object()

        settings = ImportantPagesTranslatableSiteSetting.for_site(
            self.default_site, locale=self.fr_locale
        )

        # Force site root paths query beforehand
        self.default_site.root_page._get_site_root_paths()

        for page_fk_field, expected_result in (
            ("sign_up_page", "http://localhost/"),
            ("general_terms_page", "http://localhost/"),
            ("privacy_policy_page", "http://other/"),
        ):
            with self.subTest(page_fk_field=page_fk_field):

                # only the first request for each URL will trigger queries.
                # 2 are triggered instead of 1 here, because tests use the
                # database cache backed, and the cache is queried each time
                # to fetch site root paths (because there's no 'request' to
                # store them on)

                with self.assertNumQueries(2):

                    self.assertEqual(
                        settings.get_page_url(page_fk_field), expected_result
                    )

                    # when called directly
                    self.assertEqual(
                        settings.get_page_url(page_fk_field), expected_result
                    )

                    # when called indirectly via shortcut
                    self.assertEqual(
                        getattr(settings.page_url, page_fk_field), expected_result
                    )

    def test_get_page_url_raises_attributeerror_if_attribute_name_invalid(self):
        settings = self._create_importantpagestranslatablesitesetting_object()
        # when called directly
        with self.assertRaises(AttributeError):
            settings.get_page_url("not_an_attribute")
        # when called indirectly via shortcut
        with self.assertRaises(AttributeError):
            settings.page_url.not_an_attribute

    def test_get_page_url_returns_empty_string_if_attribute_value_not_a_page(self):
        settings = self._create_importantpagestranslatablesitesetting_object()
        for value in (None, self.default_site):
            with self.subTest(attribute_value=value):
                settings.test_attribute = value
                # when called directly
                self.assertEqual(settings.get_page_url("test_attribute"), "")
                # when called indirectly via shortcut
                self.assertEqual(settings.page_url.test_attribute, "")
