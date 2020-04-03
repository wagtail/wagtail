from django.test import TestCase, override_settings

from wagtail.core.models import Site
from wagtail.tests.testapp.models import ImportantPages, TestSetting

from .base import SettingsTestMixin


@override_settings(ALLOWED_HOSTS=['localhost', 'other'])
class SettingModelTestCase(SettingsTestMixin, TestCase):

    def test_for_site_returns_expected_settings(self):
        for site, expected_site_settings in (
            (self.default_site, self.default_site_settings),
            (self.other_site, self.other_site_settings),
        ):
            with self.subTest(site=site):
                self.assertEqual(
                    TestSetting.for_site(site),
                    expected_site_settings
                )

    def test_for_request_returns_expected_settings(self):
        default_site_request = self.get_request()
        other_site_request = self.get_request(site=self.other_site)
        for request, expected_site_settings in (
            (default_site_request, self.default_site_settings),
            (other_site_request, self.other_site_settings),
        ):
            with self.subTest(request=request):
                self.assertEqual(
                    TestSetting.for_request(request),
                    expected_site_settings
                )

    def test_for_request_result_caching(self):
        # repeat test to show caching is unique per request instance,
        # even when the requests are for the same site
        for i, request in enumerate(
            [self.get_request(), self.get_request()], 1
        ):
            with self.subTest(attempt=i):

                # force site query beforehand
                Site.find_for_request(request)

                # only the first lookup should result in a query
                with self.assertNumQueries(1):
                    for i in range(4):
                        TestSetting.for_request(request)

    def _create_importantpages_object(self):
        site = self.default_site
        ImportantPages.objects.create(
            site=site,
            sign_up_page=site.root_page,
            general_terms_page=site.root_page,
            privacy_policy_page=self.other_site.root_page,
        )

    def test_select_related(self, expected_queries=4):
        """ The `select_related` attribute on setting models is `None` by default, so fetching foreign keys values requires additional queries """
        request = self.get_request()

        self._create_importantpages_object()

        # force site query beforehand
        Site.find_for_request(request)

        # fetch settings and access foreiegn keys
        with self.assertNumQueries(expected_queries):
            settings = ImportantPages.for_request(request)
            settings.sign_up_page
            settings.general_terms_page
            settings.privacy_policy_page

    def test_select_related_use_reduces_total_queries(self):
        """ But, `select_related` can be used to reduce the number of queries needed to fetch foreign keys """
        try:
            # set class attribute temporarily
            ImportantPages.select_related = ['sign_up_page', 'general_terms_page', 'privacy_policy_page']
            self.test_select_related(expected_queries=1)
        finally:
            # undo temporary change
            ImportantPages.select_related = None
