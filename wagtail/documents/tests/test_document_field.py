from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.defaultfilters import filesizeformat
from django.test import TestCase, override_settings

from wagtail.documents.fields import WagtailDocumentField


class TestWagtailDocumentField(TestCase):
    def get_field(self):
        return WagtailDocumentField()

    def get_test_file(self, size_bytes=1024, name="test.pdf"):
        return SimpleUploadedFile(
            name, b"x" * size_bytes, content_type="application/pdf"
        )

    def test_default_no_size_limit(self):
        field = self.get_field()
        self.assertIsNone(field.max_upload_size)

    def test_large_file_passes_when_no_limit(self):
        field = self.get_field()
        large_file = self.get_test_file(size_bytes=100 * 1024 * 1024)
        field.check_document_file_size(large_file)

    def test_no_help_text_when_no_limit(self):
        field = self.get_field()
        self.assertEqual(field.help_text, "")

    @override_settings(WAGTAILDOCS_MAX_UPLOAD_SIZE=1 * 1024 * 1024)
    def test_file_within_limit_passes(self):
        field = self.get_field()
        small_file = self.get_test_file(size_bytes=512 * 1024)
        field.check_document_file_size(small_file)

    @override_settings(WAGTAILDOCS_MAX_UPLOAD_SIZE=1 * 1024 * 1024)
    def test_file_exceeding_limit_raises_validation_error(self):
        field = self.get_field()
        large_file = self.get_test_file(size_bytes=2 * 1024 * 1024)
        with self.assertRaises(ValidationError) as cm:
            field.check_document_file_size(large_file)
        self.assertEqual(cm.exception.code, "file_too_large")

    @override_settings(WAGTAILDOCS_MAX_UPLOAD_SIZE=1 * 1024 * 1024)
    def test_error_message_contains_file_size(self):
        file_size_bytes = 2 * 1024 * 1024
        field = self.get_field()
        large_file = self.get_test_file(size_bytes=file_size_bytes)
        with self.assertRaises(ValidationError) as cm:
            field.check_document_file_size(large_file)
        self.assertIn(
            filesizeformat(file_size_bytes),
            cm.exception.messages[0],
        )

    @override_settings(WAGTAILDOCS_MAX_UPLOAD_SIZE=None)
    def test_none_setting_disables_limit(self):
        field = self.get_field()
        large_file = self.get_test_file(size_bytes=100 * 1024 * 1024)
        field.check_document_file_size(large_file)

    @override_settings(WAGTAILDOCS_MAX_UPLOAD_SIZE=1 * 1024 * 1024)
    def test_help_text_shown_when_limit_set(self):
        field = self.get_field()
        self.assertIn(filesizeformat(1 * 1024 * 1024), field.help_text)

    @override_settings(WAGTAILDOCS_EXTENSIONS=["pdf", "txt"])
    def test_file_with_allowed_extension_passes(self):
        field = self.get_field()
        valid_file = self.get_test_file(name="test.pdf")
        field.check_document_file_format(valid_file)

    @override_settings(WAGTAILDOCS_EXTENSIONS=["pdf", "txt"])
    def test_file_with_disallowed_extension_raises_validation_error(self):
        field = self.get_field()
        invalid_file = self.get_test_file(name="test.docx")
        with self.assertRaises(ValidationError) as cm:
            field.check_document_file_format(invalid_file)
        self.assertEqual(cm.exception.code, "invalid_document_extension")

    @override_settings(WAGTAILDOCS_EXTENSIONS=["pdf", "txt"])
    def test_help_text_shows_formats(self):
        field = self.get_field()
        self.assertEqual(field.help_text, "Supported formats: PDF, TXT.")

    @override_settings(
        WAGTAILDOCS_MAX_UPLOAD_SIZE=1 * 1024 * 1024,
        WAGTAILDOCS_EXTENSIONS=["pdf", "txt"]
    )
    def test_help_text_shows_formats_and_size(self):
        field = self.get_field()
        self.assertIn("Supported formats: PDF, TXT.", field.help_text)
        self.assertIn(filesizeformat(1 * 1024 * 1024), field.help_text)

    @override_settings(WAGTAILDOCS_EXTENSIONS=["pdf", "txt"])
    def test_error_message_contains_supported_formats(self):
        field = self.get_field()
        invalid_file = self.get_test_file(name="test.docx")
        with self.assertRaises(ValidationError) as cm:
            field.check_document_file_format(invalid_file)
        self.assertIn("Supported formats: PDF, TXT.", cm.exception.messages[0])

    def test_invalid_document_known_format_error_message(self):
        field = self.get_field()
        formatted_message = field.error_messages["invalid_document_known_format"] % {
            "extension": "pdf",
            "document_format": "txt",
        }
        self.assertEqual(
            formatted_message,
            "Not a valid .pdf document. The extension does not match the file format (txt)"
        )

    @override_settings(WAGTAILDOCS_EXTENSIONS=["pdf"])
    def test_to_python_enforces_format(self):
        field = self.get_field()
        invalid_file = self.get_test_file(name="test.docx")
        with self.assertRaises(ValidationError) as cm:
            field.to_python(invalid_file)
        self.assertEqual(cm.exception.code, "invalid_document_extension")

    @override_settings(WAGTAILDOCS_EXTENSIONS=["pdf"])
    def test_to_python_regression_valid_upload(self):
        field = self.get_field()
        valid_file = self.get_test_file(name="test.pdf")
        cleaned_file = field.to_python(valid_file)
        self.assertEqual(cleaned_file, valid_file)
