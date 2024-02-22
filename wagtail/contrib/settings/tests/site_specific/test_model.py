import pickle

from django.test import RequestFactory, TestCase, override_settings

from wagtail.models import Site
from wagtail.test.testapp.models import ImportantPagesSiteSetting, TestSiteSetting

from .base import SiteSettingsTestMixin


@override_settings(ALLOWED_HOSTS=["localhost", "other"])
class SettingModelTestCase(SiteSettingsTestMixin, TestCase):
    def test_for_site_returns_expected_settings(self):
        for site, expected_settings in (
            (self.default_site, self.default_settings),
            (self.other_site, self.other_settings),
        ):
            with self.subTest(site=site):
                self.assertEqual(TestSiteSetting.for_site(site), expected_settings)

    @override_settings(ALLOWED_HOSTS=["no-site-match.example"])
    def test_for_request_raises_does_not_exist_when_no_site_match(self):
        Site.objects.update(is_default_site=False)
        # Use RequestFactory directly, as self.get_request sets SERVER_NAME and site.
        request = RequestFactory(SERVER_NAME="no-site-match.example").get("/")
        with self.assertRaises(TestSiteSetting.DoesNotExist):
            TestSiteSetting.for_request(request)

    def test_for_site_raises_does_not_exist_when_site_is_none(self):
        with self.assertRaises(TestSiteSetting.DoesNotExist):
            TestSiteSetting.for_site(None)

    def test_for_request_returns_expected_settings(self):
        default_site_request = self.get_request()
        other_site_request = self.get_request(site=self.other_site)
        for request, expected_settings in (
            (default_site_request, self.default_settings),
            (other_site_request, self.other_settings),
        ):
            with self.subTest(request=request):
                self.assertEqual(
                    TestSiteSetting.for_request(request), expected_settings
                )

    def test_for_request_result_caching(self):
        # repeat test to show caching is unique per request instance,
        # even when the requests are for the same site
        for i, request in enumerate([self.get_request(), self.get_request()], 1):
            with self.subTest(attempt=i):
                # force site query beforehand
                Site.find_for_request(request)

                # only the first lookup should result in a query
                with self.assertNumQueries(1):
                    for i in range(4):
                        TestSiteSetting.for_request(request)

    def test_pickle_after_lookup_via_for_request(self):
        request = self.get_request()
        settings = TestSiteSetting.for_request(request)
        pickled = pickle.dumps(settings)
        unpickled = pickle.loads(pickled)
        self.assertEqual(unpickled.title, "Site title")

    def _create_importantpagessitesetting_object(self):
        site = self.default_site
        return ImportantPagesSiteSetting.objects.create(
            site=site,
            sign_up_page=site.root_page,
            general_terms_page=site.root_page,
            privacy_policy_page=self.other_site.root_page,
        )

    def test_importantpages_object_is_pickleable(self):
        obj = self._create_importantpagessitesetting_object()
        # Triggers creation of the InvokeViaAttributeShortcut instance,
        # and also gives us a value we can use for comparison
        signup_page_url = obj.page_url.sign_up_page

        # Attempt to pickle ImportantPages instance
        try:
            pickled = pickle.dumps(obj, -1)
        except Exception as e:  # noqa: BLE001
            raise AssertionError(
                f"An error occurred when attempting to pickle {obj!r}: {e}"
            )

        # Now unpickle the pickled ImportantPages
        try:
            unpickled = pickle.loads(pickled)
        except Exception as e:  # noqa: BLE001
            raise AssertionError(
                f"An error occurred when attempting to unpickle {obj!r}: {e}"
            )

        # Using 'page_url' should create a new InvokeViaAttributeShortcut
        # instance, which should give the same result as the original
        self.assertEqual(
            unpickled.page_url.sign_up_page,
            signup_page_url,
        )

    def test_select_related(self, expected_queries=4):
        """The `select_related` attribute on setting models is `None` by default, so fetching foreign keys values requires additional queries"""
        request = self.get_request()

        self._create_importantpagessitesetting_object()

        # force site query beforehand
        Site.find_for_request(request)

        # fetch settings and access foreiegn keys
        with self.assertNumQueries(expected_queries):
            settings = ImportantPagesSiteSetting.for_request(request)
            settings.sign_up_page
            settings.general_terms_page
            settings.privacy_policy_page

    def test_select_related_use_reduces_total_queries(self):
        """But, `select_related` can be used to reduce the number of queries needed to fetch foreign keys"""
        try:
            # set class attribute temporarily
            ImportantPagesSiteSetting.select_related = [
                "sign_up_page",
                "general_terms_page",
                "privacy_policy_page",
            ]
            self.test_select_related(expected_queries=1)
        finally:
            # undo temporary change
            ImportantPagesSiteSetting.select_related = None

    def test_get_page_url_when_settings_fetched_via_for_request(self):
        """Using ImportantPagesSiteSetting.for_request() makes the setting
        object request-aware, improving efficiency and allowing
        site-relative URLs to be returned"""

        self._create_importantpagessitesetting_object()

        request = self.get_request()
        settings = ImportantPagesSiteSetting.for_request(request)

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
                    # request for a URL will trigger a query to
                    # fetch the page
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
        """ImportantPagesSiteSetting.for_site() cannot make the settings object
        request-aware, so things are a little less efficient, and the
        URLs returned will not be site-relative"""
        self._create_importantpagessitesetting_object()

        settings = ImportantPagesSiteSetting.for_site(self.default_site)

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
        settings = self._create_importantpagessitesetting_object()
        # when called directly
        with self.assertRaises(AttributeError):
            settings.get_page_url("not_an_attribute")
        # when called indirectly via shortcut
        with self.assertRaises(AttributeError):
            settings.page_url.not_an_attribute

    def test_get_page_url_returns_empty_string_if_attribute_value_not_a_page(self):
        settings = self._create_importantpagessitesetting_object()
        for value in (None, self.default_site):
            with self.subTest(attribute_value=value):
                settings.test_attribute = value
                # when called directly
                self.assertEqual(settings.get_page_url("test_attribute"), "")
                # when called indirectly via shortcut
                self.assertEqual(settings.page_url.test_attribute, "")
