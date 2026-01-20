"""
Utilities for importing images from URLs.
"""

import os
from io import BytesIO
from urllib.parse import unquote, urlparse

import requests
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _


class URLImportError(Exception):
    """Base exception for URL import errors."""

    pass


class InvalidURLError(URLImportError):
    """Raised when the URL is invalid or inaccessible."""

    pass


class FileTooLargeError(URLImportError):
    """Raised when the file size exceeds the limit."""

    pass


class InvalidContentTypeError(URLImportError):
    """Raised when the content type is not a valid image type."""

    pass


class DownloadTimeoutError(URLImportError):
    """Raised when the download times out."""

    pass


# Default settings
DEFAULT_MAX_URL_DOWNLOAD_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_URL_DOWNLOAD_TIMEOUT = 30  # seconds

# Valid image content types
VALID_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    "image/bmp",
    "image/tiff",
    "image/x-icon",
    "image/vnd.microsoft.icon",
    "image/avif",
    "image/heic",
    "image/heif",
}

# Content-type to extension mapping
CONTENT_TYPE_TO_EXTENSION = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
    "image/x-icon": ".ico",
    "image/vnd.microsoft.icon": ".ico",
    "image/avif": ".avif",
    "image/heic": ".heic",
    "image/heif": ".heif",
}


def get_max_url_download_size():
    """Get the maximum file size for URL downloads."""
    return getattr(
        settings, "WAGTAILIMAGES_MAX_URL_DOWNLOAD_SIZE", DEFAULT_MAX_URL_DOWNLOAD_SIZE
    )


def get_url_download_timeout():
    """Get the timeout for URL downloads."""
    return getattr(
        settings, "WAGTAILIMAGES_URL_DOWNLOAD_TIMEOUT", DEFAULT_URL_DOWNLOAD_TIMEOUT
    )


def extract_filename_from_url(url, content_type=None):
    """
    Extract a filename from a URL.

    Args:
        url: The URL to extract the filename from.
        content_type: The Content-Type header from the response (optional).

    Returns:
        A filename string.
    """
    parsed = urlparse(url)
    path = unquote(parsed.path)

    filename = os.path.basename(path)

    if "?" in filename:
        filename = filename.split("?")[0]

    if not filename or filename == "/":
        filename = "image"

    _, ext = os.path.splitext(filename)
    if not ext and content_type:
        base_content_type = content_type.split(";")[0].strip().lower()
        ext = CONTENT_TYPE_TO_EXTENSION.get(base_content_type, "")
        if ext:
            filename = filename + ext

    return filename


def validate_url(url):
    """
    Validate that a URL is suitable for downloading.

    Args:
        url: The URL to validate.

    Raises:
        InvalidURLError: If the URL is invalid.
    """
    if not url:
        raise InvalidURLError(_("URL is required."))

    try:
        parsed = urlparse(url)
    except ValueError as e:
        raise InvalidURLError(_("Invalid URL: %(error)s") % {"error": str(e)}) from e

    if parsed.scheme not in ("http", "https"):
        raise InvalidURLError(
            _("Invalid URL scheme. Only HTTP and HTTPS URLs are supported.")
        )

    if not parsed.netloc:
        raise InvalidURLError(_("Invalid URL: missing hostname."))


def fetch_image_from_url(url):
    """
    Fetch an image from a URL and return it as an InMemoryUploadedFile.

    Args:
        url: The URL to fetch the image from.

    Returns:
        An InMemoryUploadedFile containing the image data.

    Raises:
        InvalidURLError: If the URL is invalid or inaccessible.
        FileTooLargeError: If the file exceeds the size limit.
        InvalidContentTypeError: If the content type is not a valid image.
        DownloadTimeoutError: If the download times out.
    """
    validate_url(url)

    max_size = get_max_url_download_size()
    timeout = get_url_download_timeout()

    try:
        response = requests.get(
            url,
            stream=True,
            timeout=timeout,
            headers={
                "User-Agent": "Wagtail CMS Image Importer",
            },
        )
        response.raise_for_status()

    except requests.exceptions.Timeout as e:
        raise DownloadTimeoutError(
            _("Download timed out after %(seconds)s seconds.") % {"seconds": timeout}
        ) from e
    except requests.exceptions.SSLError as e:
        raise InvalidURLError(_("SSL certificate verification failed.")) from e
    except requests.exceptions.ConnectionError as e:
        raise InvalidURLError(_("Could not connect to the server.")) from e
    except requests.exceptions.HTTPError as e:
        raise InvalidURLError(
            _("Server returned an error: %(status)s")
            % {"status": e.response.status_code}
        ) from e
    except requests.exceptions.RequestException as e:
        raise InvalidURLError(
            _("Failed to fetch URL: %(error)s") % {"error": str(e)}
        ) from e

    content_type = response.headers.get("Content-Type", "")
    base_content_type = content_type.split(";")[0].strip().lower()

    if base_content_type not in VALID_IMAGE_CONTENT_TYPES:
        raise InvalidContentTypeError(
            _("URL does not point to a valid image. Content type: %(content_type)s")
            % {"content_type": content_type or "unknown"}
        )

    content_length = response.headers.get("Content-Length")
    if content_length:
        try:
            file_size = int(content_length)
            if max_size is not None and file_size > max_size:
                raise FileTooLargeError(
                    _("File is too large (%(file_size)s). Maximum size: %(max_size)s.")
                    % {
                        "file_size": filesizeformat(file_size),
                        "max_size": filesizeformat(max_size),
                    }
                )
        except ValueError:
            pass

    file_data = BytesIO()
    bytes_downloaded = 0
    chunk_size = 8192

    for chunk in response.iter_content(chunk_size=chunk_size):
        if chunk:
            bytes_downloaded += len(chunk)

            # Check size limit during download
            if max_size is not None and bytes_downloaded > max_size:
                response.close()
                raise FileTooLargeError(
                    _("File is too large. Maximum size: %(max_size)s.")
                    % {"max_size": filesizeformat(max_size)}
                )

            file_data.write(chunk)

    response.close()

    filename = extract_filename_from_url(url, content_type)

    file_data.seek(0)

    uploaded_file = InMemoryUploadedFile(
        file=file_data,
        field_name="file",
        name=filename,
        content_type=base_content_type,
        size=bytes_downloaded,
        charset=None,
    )

    return uploaded_file
