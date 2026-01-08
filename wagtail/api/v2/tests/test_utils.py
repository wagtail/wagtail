from django.test import TestCase, override_settings

from wagtail.api.v2.utils import get_base_url


class TestGetBaseUrlPath(TestCase):
    @override_settings(WAGTAILAPI_BASE_URL="http://example.com/my-blog")
    def test_path_is_preserved(self):
        # checks for path components
        self.assertEqual(get_base_url(), "http://example.com/my-blog")

    @override_settings(WAGTAILAPI_BASE_URL="http://example.com/my-blog/")
    def test_trailing_slash_stripped(self):
        # checks for trailing slashes
        self.assertEqual(get_base_url(), "http://example.com/my-blog")

    @override_settings(WAGTAILAPI_BASE_URL="http://example.com/my-blog?foo=bar")
    def test_querystring_is_dropped(self):
        # checks for query strings
        self.assertEqual(get_base_url(), "http://example.com/my-blog")

    @override_settings(WAGTAILAPI_BASE_URL="http://example.com/my-blog#fragment")
    def test_fragment_is_dropped(self):
        # checks for fragments
        self.assertEqual(get_base_url(), "http://example.com/my-blog")

    @override_settings(WAGTAILAPI_BASE_URL="http://example.com")
    def test_simple_hostname(self):
        # checks for simple hostnames
        self.assertEqual(get_base_url(), "http://example.com")

    @override_settings(WAGTAILAPI_BASE_URL="http://example.com:8000")
    def test_hostname_with_port(self):
        # checks for ports
        self.assertEqual(get_base_url(), "http://example.com:8000")
