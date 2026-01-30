import datetime
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from wagtail.admin.views.generic.preview import PreviewOnEdit
from wagtail.models import Page, UploadedFile
from wagtail.test.testapp.models import FilePage
from wagtail.test.utils import WagtailTestUtils


class TestPreviewWithFiles(WagtailTestUtils, TestCase):
    """Test preview functionality with file uploads."""

    def setUp(self):
        self.user = self.login()
        self.home_page = Page.objects.get(url_path="/home/")
        # Create a FilePage for editing tests
        self.file_page = FilePage(title="Test File Page")
        self.home_page.add_child(instance=self.file_page)

    def test_preview_on_create_with_file_upload(self):
        """Test that file uploads are saved and accessible during preview on create."""
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_add",
            args=("tests", "filepage", self.home_page.id),
        )

        # Create a fake file
        test_file = SimpleUploadedFile(
            "test_file.txt",
            b"This is a test file content",
            content_type="text/plain",
        )

        post_data = {
            "title": "File Page with Upload",
            "slug": "file-page-upload",
        }

        # Post with files
        response = self.client.post(
            preview_url, {**post_data, "file_field": test_file}
        )

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": True, "is_available": True},
        )

        # Verify that an UploadedFile instance was created
        uploaded_files = UploadedFile.objects.filter(uploaded_by_user=self.user)
        self.assertEqual(uploaded_files.count(), 1)
        self.assertEqual(uploaded_files.first().uploaded_by_user, self.user)

        # Verify the file is accessible during preview GET
        response = self.client.get(preview_url)
        self.assertEqual(response.status_code, 200)

        # The form should have been populated with the file
        # We can verify this by checking that no error was returned
        self.assertNotContains(response, "Preview not available")

    def test_preview_on_edit_with_file_upload(self):
        """Test that file uploads work during preview on edit."""
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_edit", args=(self.file_page.id,)
        )

        # Create a fake file
        test_file = SimpleUploadedFile(
            "updated_file.txt",
            b"Updated file content",
            content_type="text/plain",
        )

        post_data = {
            "title": "Updated File Page",
            "slug": self.file_page.slug,
        }

        # Post with files
        response = self.client.post(
            preview_url, {**post_data, "file_field": test_file}
        )

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": True, "is_available": True},
        )

        # Verify that an UploadedFile instance was created
        uploaded_files = UploadedFile.objects.filter(uploaded_by_user=self.user)
        self.assertEqual(uploaded_files.count(), 1)

        # Verify the file is accessible during preview GET
        response = self.client.get(preview_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Preview not available")

    def test_preview_with_multiple_file_updates(self):
        """Test that updating file in preview updates the UploadedFile instance."""
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_edit", args=(self.file_page.id,)
        )

        # First upload
        test_file_1 = SimpleUploadedFile(
            "file1.txt", b"First file", content_type="text/plain"
        )
        post_data = {"title": "File Page", "slug": self.file_page.slug}
        response = self.client.post(
            preview_url, {**post_data, "file_field": test_file_1}
        )
        self.assertEqual(response.status_code, 200)

        # Should have 1 uploaded file
        self.assertEqual(UploadedFile.objects.count(), 1)
        first_file_id = UploadedFile.objects.first().id

        # Second upload (different file)
        test_file_2 = SimpleUploadedFile(
            "file2.txt", b"Second file", content_type="text/plain"
        )
        response = self.client.post(
            preview_url, {**post_data, "file_field": test_file_2}
        )
        self.assertEqual(response.status_code, 200)

        # Should now have 2 uploaded files (old one not cleaned up yet)
        self.assertEqual(UploadedFile.objects.count(), 2)

        # The session should reference the new file
        session_data = self.client.session.get(f"wagtail-preview-{self.file_page.id}")
        self.assertIsNotNone(session_data)
        self.assertIn("file_field", session_data[1])
        self.assertNotEqual(session_data[1]["file_field"], first_file_id)

    def test_preview_cleanup_on_delete(self):
        """Test that UploadedFile instances are cleaned up when preview is deleted."""
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_edit", args=(self.file_page.id,)
        )

        # Upload a file
        test_file = SimpleUploadedFile(
            "cleanup_test.txt", b"Test cleanup", content_type="text/plain"
        )
        post_data = {"title": "File Page", "slug": self.file_page.slug}
        self.client.post(preview_url, {**post_data, "file_field": test_file})

        # Verify file was created
        self.assertEqual(UploadedFile.objects.count(), 1)
        uploaded_file_id = UploadedFile.objects.first().id

        # Delete the preview
        response = self.client.delete(preview_url)
        self.assertEqual(response.status_code, 200)

        # Verify the UploadedFile was deleted
        self.assertEqual(UploadedFile.objects.count(), 0)
        self.assertFalse(UploadedFile.objects.filter(id=uploaded_file_id).exists())

    def test_preview_cleanup_on_expiry(self):
        """Test that expired preview data cleans up associated files."""
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_edit", args=(self.file_page.id,)
        )

        initial_datetime = timezone.now()
        expiry_datetime = initial_datetime + datetime.timedelta(
            seconds=PreviewOnEdit.preview_expiration_timeout + 1
        )

        with freeze_time(initial_datetime) as frozen_datetime:
            # Upload a file
            test_file = SimpleUploadedFile(
                "expired_test.txt", b"Test expiry", content_type="text/plain"
            )
            post_data = {"title": "File Page", "slug": self.file_page.slug}
            self.client.post(preview_url, {**post_data, "file_field": test_file})

            # Verify file was created
            self.assertEqual(UploadedFile.objects.count(), 1)
            uploaded_file_id = UploadedFile.objects.first().id

            # Move time forward past expiration
            frozen_datetime.move_to(expiry_datetime)

            # Create a new file page to trigger cleanup
            new_file_page = FilePage(title="New File Page")
            self.home_page.add_child(instance=new_file_page)
            new_preview_url = reverse(
                "wagtailadmin_pages:preview_on_edit", args=(new_file_page.id,)
            )

            # This should trigger cleanup of old preview data
            new_test_file = SimpleUploadedFile(
                "new_file.txt", b"New file", content_type="text/plain"
            )
            new_post_data = {"title": "New File Page", "slug": new_file_page.slug}
            self.client.post(
                new_preview_url, {**new_post_data, "file_field": new_test_file}
            )

            # The expired file should have been cleaned up
            self.assertFalse(UploadedFile.objects.filter(id=uploaded_file_id).exists())
            # New file should still exist
            self.assertEqual(UploadedFile.objects.count(), 1)

    def test_backward_compatibility_with_old_session_format(self):
        """Test that old session format (without file IDs) still works."""
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_edit", args=(self.file_page.id,)
        )

        # Manually set old-style session data (2-element tuple)
        from time import time

        session_key = f"wagtail-preview-{self.file_page.id}"
        post_data_encoded = f"title={self.file_page.title}&slug={self.file_page.slug}"
        self.client.session[session_key] = (post_data_encoded, time())
        self.client.session.save()

        # Try to get the preview - should not crash
        response = self.client.get(preview_url)

        # Should show preview error since we don't have valid form data
        # but it shouldn't crash from the old session format
        self.assertEqual(response.status_code, 200)

    def test_preview_without_files(self):
        """Test that preview still works when no files are uploaded."""
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_edit", args=(self.file_page.id,)
        )

        post_data = {
            "title": "Page Without File",
            "slug": self.file_page.slug,
        }

        # Post without files
        response = self.client.post(preview_url, post_data)

        # In this case, the form may be invalid if file_field is required
        # But the important thing is that it doesn't crash
        self.assertEqual(response.status_code, 200)

        # No UploadedFile instances should be created
        self.assertEqual(UploadedFile.objects.count(), 0)

    def test_preview_file_persistence_across_gets(self):
        """Test that uploaded files persist across multiple preview GET requests."""
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_edit", args=(self.file_page.id,)
        )

        # Upload a file
        test_file = SimpleUploadedFile(
            "persistent.txt", b"Persistent file", content_type="text/plain"
        )
        post_data = {"title": "File Page", "slug": self.file_page.slug}
        self.client.post(preview_url, {**post_data, "file_field": test_file})

        # Get preview multiple times
        response1 = self.client.get(preview_url)
        self.assertEqual(response1.status_code, 200)

        response2 = self.client.get(preview_url)
        self.assertEqual(response2.status_code, 200)

        response3 = self.client.get(preview_url)
        self.assertEqual(response3.status_code, 200)

        # File should still exist
        self.assertEqual(UploadedFile.objects.count(), 1)

    def test_missing_uploaded_file_handled_gracefully(self):
        """Test that missing UploadedFile instances are handled gracefully."""
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_edit", args=(self.file_page.id,)
        )

        # Upload a file
        test_file = SimpleUploadedFile(
            "temp.txt", b"Temporary", content_type="text/plain"
        )
        post_data = {"title": "File Page", "slug": self.file_page.slug}
        self.client.post(preview_url, {**post_data, "file_field": test_file})

        # Manually delete the UploadedFile (simulating external deletion)
        UploadedFile.objects.all().delete()

        # Try to get preview - should not crash
        response = self.client.get(preview_url)

        # Should still return a response (even if it shows an error)
        self.assertEqual(response.status_code, 200)
