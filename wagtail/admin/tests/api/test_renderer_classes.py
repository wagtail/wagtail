import json

from django.test import TestCase
from django.urls import reverse

from wagtail.test.utils import WagtailTestUtils


class TestPagesAdminAPIRendererClasses(WagtailTestUtils, TestCase):
    """Test that PagesAdminAPIViewSet renderer behavior works correctly."""

    def setUp(self):
        self.user = self.login()

    def test_api_response_returns_json_by_default(self):
        """Test that API returns JSON by default."""
        response = self.client.get(reverse("wagtailadmin_api:pages:listing"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Should be valid JSON
        content = json.loads(response.content.decode("UTF-8"))
        self.assertIn("meta", content)
        self.assertIn("items", content)

    def test_api_response_returns_json_with_json_accept_header(self):
        """Test that API returns JSON when JSON is explicitly requested."""
        response = self.client.get(
            reverse("wagtailadmin_api:pages:listing"), HTTP_ACCEPT="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Should be valid JSON
        content = json.loads(response.content.decode("UTF-8"))
        self.assertIn("meta", content)
        self.assertIn("items", content)

    def test_api_response_returns_html_with_html_accept_header(self):
        """Test that API returns HTML when HTML is explicitly requested via Accept header."""
        response = self.client.get(
            reverse("wagtailadmin_api:pages:listing"), HTTP_ACCEPT="text/html"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")

        # Should contain HTML content
        content = response.content.decode("UTF-8")
        self.assertIn("<html", content)
        self.assertIn("</html>", content)
