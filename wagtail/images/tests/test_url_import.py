"""
Tests for image URL import functionality.
"""

from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase, override_settings

from wagtail.images.url_import import (
    DEFAULT_MAX_URL_DOWNLOAD_SIZE,
    DownloadTimeoutError,
    FileTooLargeError,
    InvalidContentTypeError,
    InvalidURLError,
    extract_filename_from_url,
    fetch_image_from_url,
    get_max_url_download_size,
    get_url_download_timeout,
    validate_url,
)


class TestUrlImportSettings(TestCase):
    def test_get_max_url_download_size_default(self):
        self.assertEqual(get_max_url_download_size(), DEFAULT_MAX_URL_DOWNLOAD_SIZE)

    @override_settings(WAGTAILIMAGES_MAX_URL_DOWNLOAD_SIZE=5 * 1024 * 1024)
    def test_get_max_url_download_size_custom(self):
        self.assertEqual(get_max_url_download_size(), 5 * 1024 * 1024)

    def test_get_url_download_timeout_default(self):
        self.assertEqual(get_url_download_timeout(), 30)

    @override_settings(WAGTAILIMAGES_URL_DOWNLOAD_TIMEOUT=60)
    def test_get_url_download_timeout_custom(self):
        self.assertEqual(get_url_download_timeout(), 60)


class TestExtractFilenameFromUrl(TestCase):
    def test_simple_filename(self):
        url = "https://example.com/images/photo.jpg"
        self.assertEqual(extract_filename_from_url(url), "photo.jpg")

    def test_filename_with_query_string(self):
        url = "https://example.com/images/photo.jpg?width=100"
        self.assertEqual(extract_filename_from_url(url), "photo.jpg")

    def test_filename_with_encoded_characters(self):
        url = "https://example.com/images/my%20photo.jpg"
        self.assertEqual(extract_filename_from_url(url), "my photo.jpg")

    def test_no_filename_returns_image(self):
        url = "https://example.com/"
        self.assertEqual(extract_filename_from_url(url), "image")

    def test_filename_without_extension_adds_from_content_type(self):
        url = "https://example.com/images/photo"
        filename = extract_filename_from_url(url, content_type="image/jpeg")
        self.assertEqual(filename, "photo.jpg")

    def test_filename_without_extension_png(self):
        url = "https://example.com/images/photo"
        filename = extract_filename_from_url(url, content_type="image/png")
        self.assertEqual(filename, "photo.png")

    def test_content_type_with_charset(self):
        url = "https://example.com/images/photo"
        filename = extract_filename_from_url(
            url, content_type="image/jpeg; charset=utf-8"
        )
        self.assertEqual(filename, "photo.jpg")


class TestValidateUrl(TestCase):
    def test_valid_https_url(self):
        validate_url("https://example.com/image.jpg")

    def test_valid_http_url(self):
        validate_url("http://example.com/image.jpg")

    def test_empty_url_raises(self):
        with self.assertRaises(InvalidURLError):
            validate_url("")

    def test_none_url_raises(self):
        with self.assertRaises(InvalidURLError):
            validate_url(None)

    def test_ftp_url_raises(self):
        with self.assertRaises(InvalidURLError) as cm:
            validate_url("ftp://example.com/image.jpg")
        self.assertIn("HTTP and HTTPS", str(cm.exception))

    def test_file_url_raises(self):
        with self.assertRaises(InvalidURLError):
            validate_url("file:///etc/passwd")

    def test_missing_hostname_raises(self):
        with self.assertRaises(InvalidURLError) as cm:
            validate_url("https:///image.jpg")
        self.assertIn("hostname", str(cm.exception))


class TestFetchImageFromUrl(TestCase):
    def _create_mock_response(
        self,
        content=b"fake image data",
        content_type="image/jpeg",
        content_length=None,
        status_code=200,
    ):
        """Helper to create a mock response."""
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": content_type}
        if content_length is not None:
            mock_response.headers["Content-Length"] = str(content_length)
        mock_response.iter_content.return_value = [content]
        mock_response.status_code = status_code
        mock_response.raise_for_status = MagicMock()
        return mock_response

    @patch("wagtail.images.url_import.requests.get")
    def test_successful_fetch(self, mock_get):
        mock_response = self._create_mock_response(
            content=b"fake image data",
            content_type="image/jpeg",
        )
        mock_get.return_value = mock_response

        uploaded_file = fetch_image_from_url("https://example.com/image.jpg")

        self.assertEqual(uploaded_file.name, "image.jpg")
        self.assertEqual(uploaded_file.content_type, "image/jpeg")
        self.assertEqual(uploaded_file.size, len(b"fake image data"))

    @patch("wagtail.images.url_import.requests.get")
    def test_fetch_png_image(self, mock_get):
        mock_response = self._create_mock_response(
            content=b"fake png data",
            content_type="image/png",
        )
        mock_get.return_value = mock_response

        uploaded_file = fetch_image_from_url("https://example.com/photo.png")

        self.assertEqual(uploaded_file.name, "photo.png")
        self.assertEqual(uploaded_file.content_type, "image/png")

    @patch("wagtail.images.url_import.requests.get")
    def test_invalid_content_type_raises(self, mock_get):
        mock_response = self._create_mock_response(
            content=b"not an image",
            content_type="text/html",
        )
        mock_get.return_value = mock_response

        with self.assertRaises(InvalidContentTypeError) as cm:
            fetch_image_from_url("https://example.com/page.html")
        self.assertIn("text/html", str(cm.exception))

    @patch("wagtail.images.url_import.requests.get")
    def test_application_octet_stream_raises(self, mock_get):
        mock_response = self._create_mock_response(
            content=b"binary data",
            content_type="application/octet-stream",
        )
        mock_get.return_value = mock_response

        with self.assertRaises(InvalidContentTypeError):
            fetch_image_from_url("https://example.com/file.bin")

    @patch("wagtail.images.url_import.requests.get")
    @override_settings(WAGTAILIMAGES_MAX_URL_DOWNLOAD_SIZE=100)
    def test_file_too_large_from_content_length(self, mock_get):
        mock_response = self._create_mock_response(
            content=b"x" * 200,
            content_type="image/jpeg",
            content_length=200,
        )
        mock_get.return_value = mock_response

        with self.assertRaises(FileTooLargeError):
            fetch_image_from_url("https://example.com/large.jpg")

    @patch("wagtail.images.url_import.requests.get")
    @override_settings(WAGTAILIMAGES_MAX_URL_DOWNLOAD_SIZE=100)
    def test_file_too_large_during_download(self, mock_get):
        mock_response = self._create_mock_response(
            content_type="image/jpeg",
        )
        mock_response.headers = {"Content-Type": "image/jpeg"}
        mock_response.iter_content.return_value = [b"x" * 50, b"x" * 60]
        mock_get.return_value = mock_response

        with self.assertRaises(FileTooLargeError):
            fetch_image_from_url("https://example.com/large.jpg")

    @patch("wagtail.images.url_import.requests.get")
    def test_timeout_raises(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout()

        with self.assertRaises(DownloadTimeoutError):
            fetch_image_from_url("https://example.com/slow.jpg")

    @patch("wagtail.images.url_import.requests.get")
    def test_connection_error_raises(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError()

        with self.assertRaises(InvalidURLError) as cm:
            fetch_image_from_url("https://example.com/unreachable.jpg")
        self.assertIn("Could not connect", str(cm.exception))

    @patch("wagtail.images.url_import.requests.get")
    def test_ssl_error_raises(self, mock_get):
        mock_get.side_effect = requests.exceptions.SSLError()

        with self.assertRaises(InvalidURLError) as cm:
            fetch_image_from_url("https://example.com/bad-ssl.jpg")
        self.assertIn("SSL", str(cm.exception))

    @patch("wagtail.images.url_import.requests.get")
    def test_http_error_raises(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        error = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value.raise_for_status.side_effect = error

        with self.assertRaises(InvalidURLError) as cm:
            fetch_image_from_url("https://example.com/notfound.jpg")
        self.assertIn("404", str(cm.exception))

    @patch("wagtail.images.url_import.requests.get")
    def test_svg_content_type_accepted(self, mock_get):
        mock_response = self._create_mock_response(
            content=b"<svg></svg>",
            content_type="image/svg+xml",
        )
        mock_get.return_value = mock_response

        uploaded_file = fetch_image_from_url("https://example.com/icon.svg")

        self.assertEqual(uploaded_file.name, "icon.svg")
        self.assertEqual(uploaded_file.content_type, "image/svg+xml")

    @patch("wagtail.images.url_import.requests.get")
    def test_webp_content_type_accepted(self, mock_get):
        mock_response = self._create_mock_response(
            content=b"webp data",
            content_type="image/webp",
        )
        mock_get.return_value = mock_response

        uploaded_file = fetch_image_from_url("https://example.com/photo.webp")

        self.assertEqual(uploaded_file.content_type, "image/webp")

    @patch("wagtail.images.url_import.requests.get")
    def test_gif_content_type_accepted(self, mock_get):
        mock_response = self._create_mock_response(
            content=b"gif data",
            content_type="image/gif",
        )
        mock_get.return_value = mock_response

        uploaded_file = fetch_image_from_url("https://example.com/animation.gif")

        self.assertEqual(uploaded_file.content_type, "image/gif")

    @patch("wagtail.images.url_import.requests.get")
    def test_uses_user_agent(self, mock_get):
        mock_response = self._create_mock_response()
        mock_get.return_value = mock_response

        fetch_image_from_url("https://example.com/image.jpg")

        call_kwargs = mock_get.call_args[1]
        self.assertIn("User-Agent", call_kwargs["headers"])
        self.assertIn("Wagtail", call_kwargs["headers"]["User-Agent"])

    @patch("wagtail.images.url_import.requests.get")
    def test_uses_timeout(self, mock_get):
        mock_response = self._create_mock_response()
        mock_get.return_value = mock_response

        fetch_image_from_url("https://example.com/image.jpg")

        call_kwargs = mock_get.call_args[1]
        self.assertEqual(call_kwargs["timeout"], 30)

    @patch("wagtail.images.url_import.requests.get")
    @override_settings(WAGTAILIMAGES_URL_DOWNLOAD_TIMEOUT=60)
    def test_uses_custom_timeout(self, mock_get):
        mock_response = self._create_mock_response()
        mock_get.return_value = mock_response

        fetch_image_from_url("https://example.com/image.jpg")

        call_kwargs = mock_get.call_args[1]
        self.assertEqual(call_kwargs["timeout"], 60)

    @patch("wagtail.images.url_import.requests.get")
    def test_streams_response(self, mock_get):
        mock_response = self._create_mock_response()
        mock_get.return_value = mock_response

        fetch_image_from_url("https://example.com/image.jpg")

        call_kwargs = mock_get.call_args[1]
        self.assertTrue(call_kwargs["stream"])
