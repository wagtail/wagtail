import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.test.utils import WagtailTestUtils


class TestChooserUploadHidden(WagtailTestUtils, TestCase):
    """Test upload tab visibility for generic chooser"""

    def setUp(self):
        self.login()

    @override_settings(WAGTAILDOCS_EXTENSIONS=["pdf"])
    def test_upload_tab_visible_on_validation_error(self):
        """Test upload tab visibility on validation error"""

        # Upload file with invalid extension
        test_file = SimpleUploadedFile("test.txt", b"Test File")
        response = self.client.post(
            reverse("wagtaildocs_chooser:create"), {"title": "Test", "file": test_file}
        )

        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content.decode("utf-8"))

        self.assertEqual(response_json["step"], "reshow_creation_form")

        html = response_json.get("htmlFragment")
        self.assertIsNotNone(html)

        soup = self.get_soup(html)
        upload_tab = soup.find(id="tab-upload")

        self.assertIsNotNone(upload_tab)
        self.assertNotIn("hidden", upload_tab.attrs)

    def test_upload_tab_hidden_on_initial_load(self):
        """Test upload tab hidden on initial load"""
        response = self.client.get(reverse("wagtaildocs_chooser:choose"))

        response_json = json.loads(response.content.decode("utf-8"))

        html = response_json.get("html", "")
        self.assertIsNotNone(html)

        soup = self.get_soup(html)
        upload_tab = soup.find(id="tab-upload")

        self.assertIsNotNone(upload_tab)
        self.assertIn("hidden", upload_tab.attrs)
