from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.defaultfilters import filesizeformat
from django.test import TestCase, override_settings

from wagtail.documents.fields import WagtailDocumentField


class TestWagtailDocumentField(TestCase):
    def get_field(self):
        return WagtailDocumentField()

    def get_test_file(self, size_bytes=1024, name="test.pdf"):
        """Create a test file of a specific size."""
        return SimpleUploadedFile(
            name, b"x" * size_bytes, content_type="application/pdf"
        )

    # --- Default behaviour (no limit) ---

    def test_default_no_size_limit(self):
        """By default WAGTAILDOCS_MAX_UPLOAD_SIZE is None — no validation should run."""
        field = self.get_field()
        self.assertIsNone(field.max_upload_size)

    def test_large_file_passes_when_no_limit(self):
        """A large file should pass when no size limit is set."""
        field = self.get_field()
        large_file = self.get_test_file(size_bytes=100 * 1024 * 1024)  # 100MB
        # Should not raise
        field.check_document_file_size(large_file)

    def test_no_help_text_when_no_limit(self):
        """No help text should be set when there is no size limit."""
        field = self.get_field()
        self.assertEqual(field.help_text, "")

    # --- With size limit set ---

    @override_settings(WAGTAILDOCS_MAX_UPLOAD_SIZE=1 * 1024 * 1024)  # 1MB
    def test_file_within_limit_passes(self):
        """A file within the size limit should pass validation."""
        field = self.get_field()
        small_file = self.get_test_file(size_bytes=512 * 1024)  # 512KB
        # Should not raise
        field.check_document_file_size(small_file)

    @override_settings(WAGTAILDOCS_MAX_UPLOAD_SIZE=1 * 1024 * 1024)  # 1MB
    def test_file_exceeding_limit_raises_validation_error(self):
        """A file exceeding the size limit should raise a ValidationError."""
        field = self.get_field()
        large_file = self.get_test_file(size_bytes=2 * 1024 * 1024)  # 2MB
        with self.assertRaises(ValidationError) as cm:
            field.check_document_file_size(large_file)
        self.assertEqual(cm.exception.code, "file_too_large")

    @override_settings(WAGTAILDOCS_MAX_UPLOAD_SIZE=1 * 1024 * 1024)  # 1MB
    def test_error_message_contains_file_size(self):
        """The error message should contain the actual file size."""
        file_size_bytes = 2 * 1024 * 1024  # 2MB
        field = self.get_field()
        large_file = self.get_test_file(size_bytes=file_size_bytes)
        with self.assertRaises(ValidationError) as cm:
            field.check_document_file_size(large_file)
        # Check the rendered message list directly to avoid escaping issues
        self.assertIn(
            filesizeformat(file_size_bytes),
            cm.exception.messages[0],
        )

    @override_settings(WAGTAILDOCS_MAX_UPLOAD_SIZE=None)
    def test_none_setting_disables_limit(self):
        """Explicitly setting WAGTAILDOCS_MAX_UPLOAD_SIZE to None disables validation."""
        field = self.get_field()
        large_file = self.get_test_file(size_bytes=100 * 1024 * 1024)  # 100MB
        # Should not raise
        field.check_document_file_size(large_file)

    @override_settings(WAGTAILDOCS_MAX_UPLOAD_SIZE=1 * 1024 * 1024)  # 1MB
    def test_help_text_shown_when_limit_set(self):
        """Help text should be shown when a size limit is configured."""
        field = self.get_field()
        self.assertIn(filesizeformat(1 * 1024 * 1024), field.help_text)
