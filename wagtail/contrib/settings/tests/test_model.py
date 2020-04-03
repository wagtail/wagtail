from django.test import TestCase, override_settings

from wagtail.core.models import Site
from wagtail.tests.testapp.models import TestSetting

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
