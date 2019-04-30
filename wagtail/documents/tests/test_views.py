import os.path
import unittest
from unittest import mock
import urllib

from django.conf import settings
from django.core.files.base import ContentFile
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from wagtail.documents import models


class TestServeView(TestCase):
    def setUp(self):
        self.document = models.Document(title="Test document")
        self.document.file.save('example.doc', ContentFile("A boring example document"))

    def tearDown(self):
        # delete the FieldFile directly because the TestCase does not commit
        # transactions to trigger transaction.on_commit() in the signal handler
        self.document.file.delete()

    def get(self):
        return self.client.get(reverse('wagtaildocs_serve', args=(self.document.id, self.document.filename)))

    def test_response_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_content_disposition_header(self):
        self.assertEqual(
            self.get()['Content-Disposition'],
            'attachment; filename="{}"'.format(self.document.filename))

    @mock.patch('wagtail.documents.views.serve.hooks')
    @mock.patch('wagtail.documents.views.serve.get_object_or_404')
    def test_non_local_filesystem_content_disposition_header(
        self, mock_get_object_or_404, mock_hooks
    ):
        """
        Tests the 'Content-Disposition' header in a response when using a
        storage backend that doesn't expose filesystem paths.
        """
        # Create a mock document with no local file to hit the correct code path
        mock_doc = mock.Mock()
        mock_doc.filename = 'example.doc'
        mock_doc.file.path = None
        mock_get_object_or_404.return_value = mock_doc

        # Bypass 'before_serve_document' hooks
        mock_hooks.get_hooks.return_value = []

        self.assertEqual(
            self.get()['Content-Disposition'],
            "attachment; filename={0}; filename*=UTF-8''{0}".format(
                urllib.parse.quote(self.document.filename)
            )
        )

    def test_content_length_header(self):
        self.assertEqual(self.get()['Content-Length'], '25')

    def test_content_type_header(self):
        self.assertEqual(self.get()['Content-Type'], 'application/msword')

    def test_is_streaming_response(self):
        self.assertTrue(self.get().streaming)

    def test_content(self):
        self.assertEqual(b"".join(self.get().streaming_content), b"A boring example document")

    def test_document_served_fired(self):
        mock_handler = mock.MagicMock()
        models.document_served.connect(mock_handler)

        self.get()

        self.assertEqual(mock_handler.call_count, 1)
        self.assertEqual(mock_handler.mock_calls[0][2]['sender'], models.Document)
        self.assertEqual(mock_handler.mock_calls[0][2]['instance'], self.document)

    def test_with_nonexistent_document(self):
        response = self.client.get(reverse('wagtaildocs_serve', args=(1000, 'blahblahblah', )))
        self.assertEqual(response.status_code, 404)

    def test_with_incorrect_filename(self):
        response = self.client.get(reverse('wagtaildocs_serve', args=(self.document.id, 'incorrectfilename')))
        self.assertEqual(response.status_code, 404)

    def clear_sendfile_cache(self):
        from wagtail.utils.sendfile import _get_sendfile
        _get_sendfile.clear()


class TestServeViewWithSendfile(TestCase):
    def setUp(self):
        # Import using a try-catch block to prevent crashes if the
        # django-sendfile module is not installed
        try:
            import sendfile  # noqa
        except ImportError:
            raise unittest.SkipTest("django-sendfile not installed")

        self.document = models.Document(title="Test document")
        self.document.file.save('example.doc', ContentFile("A boring example document"))

    def tearDown(self):
        # delete the FieldFile directly because the TestCase does not commit
        # transactions to trigger transaction.on_commit() in the signal handler
        self.document.file.delete()

    def get(self):
        return self.client.get(reverse('wagtaildocs_serve', args=(self.document.id, self.document.filename)))

    def clear_sendfile_cache(self):
        from wagtail.utils.sendfile import _get_sendfile
        _get_sendfile.clear()

    @override_settings(SENDFILE_BACKEND='sendfile.backends.xsendfile')
    def test_sendfile_xsendfile_backend(self):
        self.clear_sendfile_cache()
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['X-Sendfile'], self.document.file.path)

    @override_settings(
        SENDFILE_BACKEND='sendfile.backends.mod_wsgi',
        SENDFILE_ROOT=settings.MEDIA_ROOT,
        SENDFILE_URL=settings.MEDIA_URL[:-1]
    )
    def test_sendfile_mod_wsgi_backend(self):
        self.clear_sendfile_cache()
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Location'], os.path.join(settings.MEDIA_URL, self.document.file.name))

    @override_settings(
        SENDFILE_BACKEND='sendfile.backends.nginx',
        SENDFILE_ROOT=settings.MEDIA_ROOT,
        SENDFILE_URL=settings.MEDIA_URL[:-1]
    )
    def test_sendfile_nginx_backend(self):
        self.clear_sendfile_cache()
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['X-Accel-Redirect'], os.path.join(settings.MEDIA_URL, self.document.file.name))


class TestServeWithUnicodeFilename(TestCase):
    def setUp(self):
        self.document = models.Document(title="Test document")

        self.filename = 'docs\u0627\u0644\u0643\u0627\u062a\u062f\u0631\u0627'
        '\u064a\u064a\u0629_\u0648\u0627\u0644\u0633\u0648\u0642'
        try:
            self.document.file.save(self.filename, ContentFile("A boring example document"))
        except UnicodeEncodeError:
            raise unittest.SkipTest("Filesystem doesn't support unicode filenames")

    def tearDown(self):
        # delete the FieldFile directly because the TestCase does not commit
        # transactions to trigger transaction.on_commit() in the signal handler
        self.document.file.delete()

    def test_response_code(self):
        response = self.client.get(reverse('wagtaildocs_serve', args=(self.document.id, self.filename)))
        self.assertEqual(response.status_code, 200)

    @mock.patch('wagtail.documents.views.serve.hooks')
    @mock.patch('wagtail.documents.views.serve.get_object_or_404')
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
        mock_doc.filename = 'TÈST.doc'
        mock_doc.file.path = None
        mock_get_object_or_404.return_value = mock_doc

        # Bypass 'before_serve_document' hooks
        mock_hooks.get_hooks.return_value = []

        response = self.client.get(reverse('wagtaildocs_serve', args=(self.document.id, mock_doc.filename)))

        try:
            response['Content-Disposition'].encode('ascii')
        except UnicodeDecodeError:
            self.fail('Content-Disposition with unicode characters failed ascii encoding.')

        try:
            response['Content-Disposition'].encode('latin-1')
        except UnicodeDecodeError:
            self.fail('Content-Disposition with unicode characters failed latin-1 encoding.')
