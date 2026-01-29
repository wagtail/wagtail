from django.test import TestCase, override_settings

from wagtail.api.v2.utils import get_base_url
from wagtail.models import Page, Site
from wagtail.test.utils import WagtailTestUtils


class TestGetBaseUrlPath(TestCase):
    # unit tests for the helper function
    @override_settings(
        WAGTAILAPI_BASE_URL="http://example.com/my-blog", WAGTAILAPI_ALLOW_URL_PATH=True
    )
    def test_path_is_preserved(self):
        self.assertEqual(get_base_url(), "http://example.com/my-blog")

    @override_settings(
        WAGTAILAPI_BASE_URL="http://example.com/my-blog/",
        WAGTAILAPI_ALLOW_URL_PATH=True,
    )
    def test_trailing_slash_stripped(self):
        self.assertEqual(get_base_url(), "http://example.com/my-blog")

    @override_settings(
        WAGTAILAPI_BASE_URL="http://example.com/my-blog?foo=bar",
        WAGTAILAPI_ALLOW_URL_PATH=True,
    )
    def test_querystring_is_dropped(self):
        self.assertEqual(get_base_url(), "http://example.com/my-blog")

    @override_settings(
        WAGTAILAPI_BASE_URL="http://example.com/my-blog#fragment",
        WAGTAILAPI_ALLOW_URL_PATH=True,
    )
    def test_fragment_is_dropped(self):
        self.assertEqual(get_base_url(), "http://example.com/my-blog")

    @override_settings(WAGTAILAPI_BASE_URL="http://example.com")
    def test_simple_hostname(self):
        self.assertEqual(get_base_url(), "http://example.com")

    @override_settings(WAGTAILAPI_BASE_URL="http://example.com:8000")
    def test_hostname_with_port(self):
        self.assertEqual(get_base_url(), "http://example.com:8000")

    @override_settings(
        WAGTAILAPI_BASE_URL="http://example.com/api", WAGTAILAPI_ALLOW_URL_PATH=True
    )
    def test_path_preserved_with_flag(self):
        self.assertEqual(get_base_url(), "http://example.com/api")

    @override_settings(
        WAGTAILAPI_BASE_URL="http://example.com/api", WAGTAILAPI_ALLOW_URL_PATH=False
    )
    def test_path_stripped_without_flag_and_warning_issued(self):
        with self.assertWarns(UserWarning):
            self.assertEqual(get_base_url(), "http://example.com")


class TestFindViewRedirects(TestCase, WagtailTestUtils):
    # unit tests for find API integration testing
    def setUp(self):
        root = Page.get_first_root_node()

        self.home_page = Page(title="Test Home", slug="test-home")
        root.add_child(instance=self.home_page)

        Site.objects.filter(is_default_site=True).delete()

        Site.objects.create(
            hostname="testserver",
            root_page=self.home_page,
            is_default_site=True,
            port=80,
        )

    @override_settings(
        WAGTAILAPI_BASE_URL="http://external.com/api-path",
        WAGTAILAPI_ALLOW_URL_PATH=True,
    )
    def test_find_redirect_includes_base_url_path(self):
        response = self.client.get("/api/v2/pages/find/", {"html_path": "/"})
        self.assertEqual(response.status_code, 302)

        self.assertIn("http://external.com/api-path", response["Location"])
        self.assertIn(f"/api/v2/pages/{self.home_page.id}/", response["Location"])

    @override_settings(
        WAGTAILAPI_BASE_URL="http://external.com/api-path",
        WAGTAILAPI_ALLOW_URL_PATH=False,
    )
    def test_find_redirect_strips_path_without_flag(self):
        with self.assertWarns(UserWarning):
            response = self.client.get("/api/v2/pages/find/", {"html_path": "/"})

        self.assertEqual(response.status_code, 302)
        self.assertNotIn("/api-path", response["Location"])
        self.assertIn(
            f"http://external.com/api/v2/pages/{self.home_page.id}/",
            response["Location"],
        )
