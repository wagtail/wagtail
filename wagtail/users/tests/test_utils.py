from django.test import TestCase, override_settings

from wagtail.users.utils import get_gravatar_url


class TestGravatar(TestCase):
    def test_gravatar_default(self):
        """Test with the default settings"""
        self.assertEqual(
            get_gravatar_url("something@example.com"),
            "//www.gravatar.com/avatar/76ebd6fecabc982c205dd056e8f0415a?d=mp&s=100",
        )

    def test_gravatar_custom_size(self):
        """Test with a custom size (note that the size will be doubled)"""
        self.assertEqual(
            get_gravatar_url("something@example.com", size=100),
            "//www.gravatar.com/avatar/76ebd6fecabc982c205dd056e8f0415a?d=mp&s=200",
        )

    @override_settings(
        WAGTAIL_GRAVATAR_PROVIDER_URL="https://robohash.org/avatar?d=robohash&s=200"
    )
    def test_gravatar_params_that_overlap(self):
        """
        Test with params that overlap with default s (size) and d (default_image)
        Also test the `s` is not overridden by the provider URL's query parameters.
        """
        self.assertEqual(
            get_gravatar_url("something@example.com", size=80),
            "https://robohash.org/avatar/76ebd6fecabc982c205dd056e8f0415a?d=robohash&s=160",
        )

    @override_settings(WAGTAIL_GRAVATAR_PROVIDER_URL="https://robohash.org/avatar?f=y")
    def test_gravatar_params_that_dont_overlap(self):
        """Test with params that don't default `s (size)` and `d (default_image)`"""
        self.assertEqual(
            get_gravatar_url("something@example.com"),
            "https://robohash.org/avatar/76ebd6fecabc982c205dd056e8f0415a?d=mp&f=y&s=100",
        )

    @override_settings(
        WAGTAIL_GRAVATAR_PROVIDER_URL="https://robohash.org/avatar?d=robohash&f=y"
    )
    def test_gravatar_query_params_override_default_params(self):
        """Test that query parameters of `WAGTAIL_GRAVATAR_PROVIDER_URL` override default_params"""
        self.assertEqual(
            get_gravatar_url(
                "something@example.com", default_params={"d": "monsterid"}
            ),
            "https://robohash.org/avatar/76ebd6fecabc982c205dd056e8f0415a?d=robohash&f=y&s=100",
        )

    @override_settings(WAGTAIL_GRAVATAR_PROVIDER_URL="https://robohash.org/avatar/")
    def test_gravatar_trailing_slash(self):
        """Test with a trailing slash in the URL"""
        self.assertEqual(
            get_gravatar_url("something@example.com"),
            "https://robohash.org/avatar/76ebd6fecabc982c205dd056e8f0415a?d=mp&s=100",
        )

    @override_settings(WAGTAIL_GRAVATAR_PROVIDER_URL="https://robohash.org/avatar")
    def test_gravatar_no_trailing_slash(self):
        """Test with no trailing slash in the URL"""
        self.assertEqual(
            get_gravatar_url("something@example.com"),
            "https://robohash.org/avatar/76ebd6fecabc982c205dd056e8f0415a?d=mp&s=100",
        )

    @override_settings(WAGTAIL_GRAVATAR_PROVIDER_URL="https://robohash.org/avatar?")
    def test_gravatar_trailing_question_mark(self):
        """Test with a trailing question mark in the URL"""
        self.assertEqual(
            get_gravatar_url("something@example.com"),
            "https://robohash.org/avatar/76ebd6fecabc982c205dd056e8f0415a?d=mp&s=100",
        )
