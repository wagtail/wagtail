from django.test import TestCase, override_settings

from wagtail.api.v2.utils import get_base_url


class TestGetBaseUrlPath(TestCase):
    @override_settings(WAGTAILAPI_BASE_URL="http://example.com/my-blog")
    def test_path_is_preserved(self):
        self.assertEqual(get_base_url(), "http://example.com/my-blog")

    @override_settings(WAGTAILAPI_BASE_URL="http://example.com/my-blog/")
    def test_trailing_slash_stripped(self):
        self.assertEqual(get_base_url(), "http://example.com/my-blog")
