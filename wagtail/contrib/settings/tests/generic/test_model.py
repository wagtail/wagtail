from django.test import TestCase, override_settings

from wagtail.models import Site
from wagtail.test.testapp.models import ImportantPagesGenericSetting

from .base import GenericSettingsTestMixin


@override_settings(ALLOWED_HOSTS=["localhost", "other"])
class GenericSettingModelTestCase(GenericSettingsTestMixin, TestCase):
    def _create_importantpagesgenericsetting_object(self):
        return ImportantPagesGenericSetting.objects.create(
            sign_up_page=self.default_site.root_page,
            general_terms_page=self.default_site.root_page,
            privacy_policy_page=self.other_site.root_page,
        )

    def test_request_or_site_with_site_returns_expected_settings(self):
        for site, expected_settings in (
            (self.default_site, self.default_settings),
            (self.other_site, self.default_settings),
        ):
            with self.subTest(site=site):
                self.assertEqual(
                    self.default_settings.load(request_or_site=site),
                    expected_settings,
                )

    def test_request_or_site_with_request_returns_expected_settings(self):
        default_site_request = self.get_request()
        other_site_request = self.get_request(site=self.other_site)

        for request, expected_settings in (
            (default_site_request, self.default_settings),
            (other_site_request, self.default_settings),
        ):
            with self.subTest(request=request):
                self.assertEqual(
                    self.default_settings.load(request_or_site=request),
                    expected_settings,
                )

    def test_request_or_site_with_request_result_caching(self):
        # repeat test to show caching is unique per request instance,
        # even when the requests are for the same site
        for i, request in enumerate([self.get_request(), self.get_request()], 1):
            with self.subTest(attempt=i):
                # force site query beforehand
                Site.find_for_request(request)

                # only the first lookup should result in a query
                with self.assertNumQueries(1):
                    for i in range(4):
                        self.default_settings.load(request_or_site=request)

    def test_select_related(self, expected_queries=4):
        """The `select_related` attribute on setting models is `None` by default, so fetching foreign keys values requires additional queries"""
        self._create_importantpagesgenericsetting_object()

        # fetch settings and access foreign keys
        with self.assertNumQueries(expected_queries):
            settings = ImportantPagesGenericSetting.load()
            settings.sign_up_page
            settings.general_terms_page
            settings.privacy_policy_page

    def test_select_related_use_reduces_total_queries(self):
        """But, `select_related` can be used to reduce the number of queries needed to fetch foreign keys"""
        try:
            # set class attribute temporarily
            ImportantPagesGenericSetting.select_related = [
                "sign_up_page",
                "general_terms_page",
                "privacy_policy_page",
            ]
            self.test_select_related(expected_queries=1)
        finally:
            # undo temporary change
            ImportantPagesGenericSetting.select_related = None

    def test_get_page_url_returns_page_urls(self):
        self._create_importantpagesgenericsetting_object()

        settings = ImportantPagesGenericSetting.load()

        for page_fk_field, expected_result in (
            ("sign_up_page", "http://localhost/"),
            ("general_terms_page", "http://localhost/"),
            ("privacy_policy_page", "http://other/"),
        ):
            with self.subTest(page_fk_field=page_fk_field):
                self.assertEqual(settings.get_page_url(page_fk_field), expected_result)

                self.assertEqual(
                    getattr(settings.page_url, page_fk_field), expected_result
                )

    def test_get_page_url_raises_attributeerror_if_attribute_name_invalid(self):
        settings = self._create_importantpagesgenericsetting_object()
        # when called directly
        with self.assertRaises(AttributeError):
            settings.get_page_url("not_an_attribute")
        # when called indirectly via shortcut
        with self.assertRaises(AttributeError):
            settings.page_url.not_an_attribute

    def test_get_page_url_returns_empty_string_if_attribute_value_not_a_page(self):
        settings = self._create_importantpagesgenericsetting_object()
        for value in (None, self.default_site):
            with self.subTest(attribute_value=value):
                settings.test_attribute = value
                # when called directly
                self.assertEqual(settings.get_page_url("test_attribute"), "")
                # when called indirectly via shortcut
                self.assertEqual(settings.page_url.test_attribute, "")

    def test_display_as_string(self):
        self._create_importantpagesgenericsetting_object()

        self.assertEqual(
            str(ImportantPagesGenericSetting.load()),
            "important pages settings",
        )
