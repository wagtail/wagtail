import os.path
import unittest
import urllib
from unittest import mock

from django.conf import settings
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.documents import models


@override_settings(WAGTAILDOCS_SERVE_METHOD=None)
class TestServeView(TestCase):
    def setUp(self):
        self.document = models.Document(title="Test document", file_hash="123456")
        self.document.file.save(
            "serve_view.doc", ContentFile(b"A boring example document")
        )
        self.pdf_document = models.Document(title="Test document", file_hash="123456")
        self.pdf_document.file.save(
            "serve_view.pdf", ContentFile(b"A boring example document")
        )

    def tearDown(self):
        if hasattr(self, "response"):
            # Make sure the response is fully read before deleting the document so
            # that the file is closed by the view.
            # This is required on Windows as the below line that deletes the file
            # will crash if the file is still open.
            b"".join(self.response.streaming_content)

        # delete the FieldFile directly because the TestCase does not commit
        # transactions to trigger transaction.on_commit() in the signal handler
        self.document.file.delete()
        self.pdf_document.file.delete()

    def get(self, document=None):
        document = document or self.document
        self.response = self.client.get(
            reverse("wagtaildocs_serve", args=(document.id, document.filename))
        )
        return self.response

    def test_response_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_content_disposition_header(self):
        self.assertEqual(
            self.get(self.document)["Content-Disposition"],
            f'attachment; filename="{self.document.filename}"',
        )

    def test_inline_content_disposition_header(self):
        self.assertEqual(
            self.get(self.pdf_document)["Content-Disposition"],
            f'inline; filename="{self.pdf_document.filename}"',
        )

    def test_content_security_policy(self):
        self.assertEqual(self.get()["Content-Security-Policy"], "default-src 'none'")

        with self.settings(WAGTAILDOCS_BLOCK_EMBEDDED_CONTENT=False):
            self.assertNotIn("Content-Security-Policy", self.get().headers)

    def test_no_sniff_content_type(self):
        self.assertEqual(self.get()["X-Content-Type-Options"], "nosniff")

    @mock.patch("wagtail.documents.views.serve.hooks")
    @mock.patch("wagtail.documents.views.serve.get_object_or_404")
    def test_non_local_filesystem_headers(self, mock_get_object_or_404, mock_hooks):
        # Create a mock document with no local file to hit the correct code path
        mock_doc = mock.Mock()
        mock_doc.filename = self.document.filename
        mock_doc.content_type = self.document.content_type
        mock_doc.content_disposition = self.document.content_disposition
        mock_doc.file = ContentFile(b"file-like object" * 10)
        mock_doc.file.path = None
        mock_doc.file.url = None
        mock_get_object_or_404.return_value = mock_doc

        # Bypass 'before_serve_document' hooks
        mock_hooks.get_hooks.return_value = []

        response = self.get()

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response["Content-Disposition"],
            "attachment; filename={0}; filename*=UTF-8''{0}".format(
                urllib.parse.quote(self.document.filename)
            ),
        )
        self.assertEqual(response["Content-Security-Policy"], "default-src 'none'")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    @mock.patch("wagtail.documents.views.serve.hooks")
    @mock.patch("wagtail.documents.views.serve.get_object_or_404")
    def test_non_local_filesystem_inline_headers(
        self, mock_get_object_or_404, mock_hooks
    ):
        # Create a mock document with no local file to hit the correct code path
        mock_doc = mock.Mock()
        mock_doc.filename = self.pdf_document.filename
        mock_doc.content_type = self.pdf_document.content_type
        mock_doc.content_disposition = self.pdf_document.content_disposition
        mock_doc.file = ContentFile(b"file-like object" * 10)
        mock_doc.file.path = None
        mock_doc.file.url = None
        mock_get_object_or_404.return_value = mock_doc

        # Bypass 'before_serve_document' hooks
        mock_hooks.get_hooks.return_value = []

        response = self.get(self.pdf_document)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response["Content-Disposition"], "inline")
        self.assertEqual(response["Content-Security-Policy"], "default-src 'none'")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    def test_content_length_header(self):
        self.assertEqual(self.get()["Content-Length"], "25")

    def test_content_type_header(self):
        self.assertEqual(self.get()["Content-Type"], "application/msword")

    def test_is_streaming_response(self):
        self.assertTrue(self.get().streaming)

    def test_content(self):
        self.assertEqual(
            b"".join(self.get().streaming_content), b"A boring example document"
        )

    def test_document_served_fired(self):
        mock_handler = mock.MagicMock()
        models.document_served.connect(mock_handler)

        try:
            self.get()

            self.assertEqual(mock_handler.call_count, 1)
            self.assertEqual(mock_handler.mock_calls[0][2]["sender"], models.Document)
            self.assertEqual(mock_handler.mock_calls[0][2]["instance"], self.document)
        finally:
            models.document_served.disconnect(mock_handler)

    def test_with_nonexistent_document(self):
        response = self.client.get(
            reverse(
                "wagtaildocs_serve",
                args=(
                    1000,
                    "blahblahblah",
                ),
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_with_incorrect_filename(self):
        response = self.client.get(
            reverse("wagtaildocs_serve", args=(self.document.id, "incorrectfilename"))
        )
        self.assertEqual(response.status_code, 404)

    def test_has_etag_header(self):
        self.assertEqual(self.get()["ETag"], '"123456"')

    def clear_sendfile_cache(self):
        from wagtail.utils.sendfile import _get_sendfile

        _get_sendfile.clear()


@override_settings(WAGTAILDOCS_SERVE_METHOD="redirect")
class TestServeViewWithRedirect(TestCase):
    def setUp(self):
        self.document = models.Document(title="Test document")
        self.document.file.save(
            "serve_view_with_redirect.doc",
            ContentFile("A boring example document"),
        )
        self.serve_view_url = reverse(
            "wagtaildocs_serve", args=(self.document.id, self.document.filename)
        )

    def tearDown(self):
        self.document.delete()

    def get(self):
        return self.client.get(
            reverse(
                "wagtaildocs_serve", args=(self.document.id, self.document.filename)
            )
        )

    def test_document_url_should_point_to_serve_view(self):
        self.assertEqual(self.document.url, self.serve_view_url)

    def test_redirect(self):
        response = self.get()
        self.assertRedirects(
            response, self.document.file.url, fetch_redirect_response=False
        )


@override_settings(WAGTAILDOCS_SERVE_METHOD="direct")
class TestDirectDocumentUrls(TestCase):
    def setUp(self):
        self.document = models.Document(title="Test document")
        self.document.file.save(
            "direct_document_urls.doc",
            ContentFile("A boring example document"),
        )

    def tearDown(self):
        self.document.delete()

    def get(self):
        return self.client.get(
            reverse(
                "wagtaildocs_serve", args=(self.document.id, self.document.filename)
            )
        )

    def test_url_should_point_directly_to_file_storage_url(self):
        self.assertEqual(self.document.url, self.document.file.url)

    def test_redirect(self):
        # The serve view will not normally be linked to in 'direct' mode, but we should ensure it
        # still works by redirecting
        response = self.get()
        self.assertRedirects(
            response, self.document.file.url, fetch_redirect_response=False
        )


@override_settings(
    WAGTAILDOCS_SERVE_METHOD=None,
    STORAGES={
        **settings.STORAGES,
        "default": {
            "BACKEND": "wagtail.test.dummy_external_storage.DummyExternalStorage"
        },
    },
)
class TestServeWithExternalStorage(TestCase):
    """
    Test the behaviour of the default serve method when used with a remote storage backend
    (i.e. one that throws NotImplementedError for the path() method).
    """

    def setUp(self):
        self.document = models.Document(title="Test document")
        self.document.file.save(
            "serve_with_external_storage.doc",
            ContentFile("A boring example document"),
        )
        self.serve_view_url = reverse(
            "wagtaildocs_serve", args=(self.document.id, self.document.filename)
        )

    def tearDown(self):
        self.document.delete()

    def test_document_url_should_point_to_serve_view(self):
        self.assertEqual(self.document.url, self.serve_view_url)

    def test_redirect(self):
        # serve view should redirect to the remote URL
        response = self.client.get(self.serve_view_url)
        self.assertRedirects(
            response, self.document.file.url, fetch_redirect_response=False
        )


@override_settings(WAGTAILDOCS_SERVE_METHOD=None)
class TestServeViewWithSendfile(TestCase):
    def setUp(self):
        # Import using a try-catch block to prevent crashes if the
        # django-sendfile module is not installed
        try:
            import sendfile  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("django-sendfile not installed")

        self.document = models.Document(title="Test document")
        self.document.file.save(
            "serve_view_with_sendfile.doc",
            ContentFile("A boring example document"),
        )

    def tearDown(self):
        # delete the FieldFile directly because the TestCase does not commit
        # transactions to trigger transaction.on_commit() in the signal handler
        self.document.file.delete()

    def get(self):
        return self.client.get(
            reverse(
                "wagtaildocs_serve", args=(self.document.id, self.document.filename)
            )
        )

    def clear_sendfile_cache(self):
        from wagtail.utils.sendfile import _get_sendfile

        _get_sendfile.clear()

    @override_settings(SENDFILE_BACKEND="sendfile.backends.xsendfile")
    def test_sendfile_xsendfile_backend(self):
        self.clear_sendfile_cache()
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Sendfile"], self.document.file.path)

    @override_settings(
        SENDFILE_BACKEND="sendfile.backends.mod_wsgi",
        SENDFILE_ROOT=settings.MEDIA_ROOT,
        SENDFILE_URL=settings.MEDIA_URL[:-1],
    )
    def test_sendfile_mod_wsgi_backend(self):
        self.clear_sendfile_cache()
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Location"],
            os.path.join(settings.MEDIA_URL, self.document.file.name),
        )

    @override_settings(
        SENDFILE_BACKEND="sendfile.backends.nginx",
        SENDFILE_ROOT=settings.MEDIA_ROOT,
        SENDFILE_URL=settings.MEDIA_URL[:-1],
    )
    def test_sendfile_nginx_backend(self):
        self.clear_sendfile_cache()
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["X-Accel-Redirect"],
            os.path.join(settings.MEDIA_URL, self.document.file.name),
        )

    def test_content_security_policy(self):
        self.assertEqual(self.get()["Content-Security-Policy"], "default-src 'none'")

    def test_no_sniff_content_type(self):
        self.assertEqual(self.get()["X-Content-Type-Options"], "nosniff")


@override_settings(WAGTAILDOCS_SERVE_METHOD=None)
class TestServeWithUnicodeFilename(TestCase):
    def setUp(self):
        self.document = models.Document(title="Test document")

        self.filename = "docs\u0627\u0644\u0643\u0627\u062a\u062f\u0631\u0627"
        "\u064a\u064a\u0629_\u0648\u0627\u0644\u0633\u0648\u0642"
        try:
            self.document.file.save(
                self.filename, ContentFile("A boring example document")
            )
        except UnicodeEncodeError:
            raise unittest.SkipTest("Filesystem doesn't support unicode filenames")

    def tearDown(self):
        # delete the FieldFile directly because the TestCase does not commit
        # transactions to trigger transaction.on_commit() in the signal handler
        self.document.file.delete()

    def test_response_code(self):
        response = self.client.get(
            reverse("wagtaildocs_serve", args=(self.document.id, self.filename))
        )
        self.assertEqual(response.status_code, 200)

    @mock.patch("wagtail.documents.views.serve.hooks")
    @mock.patch("wagtail.documents.views.serve.get_object_or_404")
    def test_non_local_filesystem_unicode_content_disposition_header(
        self, mock_get_object_or_404, mock_hooks
    ):
        """
        Tests that a unicode 'Content-Disposition' header (for a response using
        a storage backend that doesn't expose filesystem paths) doesn't cause an
        error if encoded differently.
        """
        # Create a mock document to hit the correct code path.
        mock_doc = mock.Mock()
        mock_doc.filename = "TÈST.doc"
        mock_doc.file = ContentFile(b"file-like object" * 10)
        mock_doc.file.path = None
        mock_doc.file.url = None
        mock_get_object_or_404.return_value = mock_doc

        # Bypass 'before_serve_document' hooks
        mock_hooks.get_hooks.return_value = []

        response = self.client.get(
            reverse("wagtaildocs_serve", args=(self.document.id, mock_doc.filename))
        )

        self.assertEqual(response.status_code, 200)

        try:
            response["Content-Disposition"].encode("ascii")
        except UnicodeDecodeError:
            self.fail(
                "Content-Disposition with unicode characters failed ascii encoding."
            )

        try:
            response["Content-Disposition"].encode("latin-1")
        except UnicodeDecodeError:
            self.fail(
                "Content-Disposition with unicode characters failed latin-1 encoding."
            )
