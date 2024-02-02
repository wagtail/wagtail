from django.conf import settings
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.documents import models


class TestCorrectDownloadUrlSerialization(TestCase):

    """Test asserts that in case of both `redirect` and `direct`
    WAGTAILDOCS_SERVE_METHOD settings `download_url` field
    is correctly serialized by DocumentDownloadUrlField."""

    def setUp(self):
        self.document = models.Document(title="Test document", file_hash="123456")
        self.document.file.save(
            "serialization.doc",
            ContentFile("A boring example document"),
        )

    def tearDown(self):
        # delete the FieldFile directly because the TestCase does not commit
        # transactions to trigger transaction.on_commit() in the signal handler
        self.document.file.delete()

    def get_response(self, document_id, **params):
        return self.client.get(
            reverse("wagtailapi_v2:documents:detail", args=(document_id,)), params
        )

    @override_settings(
        WAGTAILDOCS_SERVE_METHOD="redirect",
        STORAGES={
            **settings.STORAGES,
            "default": {
                "BACKEND": "wagtail.test.dummy_external_storage.DummyExternalStorage"
            },
        },
        WAGTAILAPI_BASE_URL="http://example.com/",
    )
    def test_serializer_wagtaildocs_serve_redirect(self):
        response = self.get_response(self.document.id)
        data = response.json()
        self.assertIn("meta", data)
        meta = data["meta"]
        self.assertIn("download_url", meta)
        download_url = meta["download_url"]
        expected_url = (
            f"http://example.com/documents/{self.document.pk}/serialization.doc"
        )
        self.assertEqual(download_url, expected_url)

    @override_settings(
        WAGTAILDOCS_SERVE_METHOD="direct",
        STORAGES={
            **settings.STORAGES,
            "default": {
                "BACKEND": "wagtail.test.dummy_external_storage.DummyExternalStorage"
            },
        },
        MEDIA_URL="http://remotestorage.com/media/",
        WAGTAILAPI_BASE_URL="http://example.com/",
    )
    def test_serializer_wagtaildocs_serve_direct(self):
        response = self.get_response(self.document.id)
        data = response.json()
        self.assertIn("meta", data)
        meta = data["meta"]
        self.assertIn("download_url", meta)
        download_url = meta["download_url"]
        self.assertEqual(
            download_url,
            "http://remotestorage.com/media/documents/serialization.doc",
        )
