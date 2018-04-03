import os.path
import unittest

import mock
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from wagtail.documents import models
from wagtail.tests.utils import WagtailTestUtils


class TestEditView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        self.document = models.Document(title='Test')
        self.document.file.save('test_edit_view.txt',
                                ContentFile('A test content.'))
        self.edit_url = reverse('wagtaildocs:edit', args=(self.document.pk,))
        self.storage = self.document.file.storage

    def update_from_db(self):
        self.document = models.Document.objects.get(pk=self.document.pk)

    def test_reupload_same_name(self):
        """
        Checks that reuploading the document file with the same file name
        changes the file name, to avoid browser cache issues (see #3816).
        """
        old_file = self.document.file
        new_name = self.document.filename
        new_file = SimpleUploadedFile(new_name, b'An updated test content.')

        response = self.client.post(self.edit_url, {
            'title': self.document.title, 'file': new_file,
        })
        self.assertRedirects(response, reverse('wagtaildocs:index'))
        self.update_from_db()
        self.assertFalse(self.storage.exists(old_file.name))
        self.assertTrue(self.storage.exists(self.document.file.name))
        self.assertNotEqual(self.document.file.name, 'documents/' + new_name)
        self.assertEqual(self.document.file.read(),
                         b'An updated test content.')

    def test_reupload_different_name(self):
        """
        Checks that reuploading the document file with a different file name
        correctly uses the new file name.
        """
        old_file = self.document.file
        new_name = 'test_reupload_different_name.txt'
        new_file = SimpleUploadedFile(new_name, b'An updated test content.')

        response = self.client.post(self.edit_url, {
            'title': self.document.title, 'file': new_file,
        })
        self.assertRedirects(response, reverse('wagtaildocs:index'))
        self.update_from_db()
        self.assertFalse(self.storage.exists(old_file.name))
        self.assertTrue(self.storage.exists(self.document.file.name))
        self.assertEqual(self.document.file.name, 'documents/' + new_name)
        self.assertEqual(self.document.file.read(),
                         b'An updated test content.')


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

    def test_response_code(self):
        response = self.client.get(reverse('wagtaildocs_serve', args=(self.document.id, self.filename)))
        self.assertEqual(response.status_code, 200)
