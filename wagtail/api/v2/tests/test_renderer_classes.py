import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from wagtail.api.v2.views import BaseAPIViewSet
from wagtail.test.utils import WagtailTestUtils


class TestBaseAPIViewSetRendererClasses(WagtailTestUtils, TestCase):
    """Test that BaseAPIViewSet renderer behavior works correctly."""

    def setUp(self):
        self.user = self.login()

    def test_renderer_classes_with_rest_framework_installed(self):
        """Test that both JSONRenderer and BrowsableAPIRenderer are included when rest_framework is installed."""
        viewset = BaseAPIViewSet()
        renderer_classes = viewset.renderer_classes

        # Should have both renderers when rest_framework is installed
        from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer

        self.assertEqual(len(renderer_classes), 2)
        self.assertIn(JSONRenderer, renderer_classes)
        self.assertIn(BrowsableAPIRenderer, renderer_classes)

    @patch("wagtail.api.v2.views.apps.is_installed")
    def test_renderer_classes_without_rest_framework(self, mock_is_installed):
        """Test that only JSONRenderer is included when rest_framework is not installed."""

        # Mock rest_framework as not installed
        def mock_installed(app):
            return app != "rest_framework"

        mock_is_installed.side_effect = mock_installed

        viewset = BaseAPIViewSet()
        renderer_classes = viewset.renderer_classes

        # Should only have JSONRenderer when rest_framework is not installed
        from rest_framework.renderers import JSONRenderer

        self.assertEqual(len(renderer_classes), 1)
        self.assertIn(JSONRenderer, renderer_classes)

    def test_api_response_returns_json_by_default(self):
        """Test that API returns JSON by default."""
        response = self.client.get(reverse("wagtailapi_v2:pages:listing"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Should be valid JSON
        content = json.loads(response.content.decode("UTF-8"))
        self.assertIn("meta", content)
        self.assertIn("items", content)

    def test_api_response_returns_json_with_json_accept_header(self):
        """Test that API returns JSON when JSON is explicitly requested."""
        response = self.client.get(
            reverse("wagtailapi_v2:pages:listing"), HTTP_ACCEPT="application/json"
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
            reverse("wagtailapi_v2:pages:listing"), HTTP_ACCEPT="text/html"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")

        # Should contain HTML content
        content = response.content.decode("UTF-8")
        self.assertIn("<html", content)
        self.assertIn("</html>", content)

    def test_api_response_returns_html_with_browser_accept_header(self):
        """Test that API returns HTML when accessed with typical browser Accept headers."""
        response = self.client.get(
            reverse("wagtailapi_v2:pages:listing"),
            HTTP_ACCEPT="text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")

        # Should contain HTML content
        content = response.content.decode("UTF-8")
        self.assertIn("<html", content)
        self.assertIn("</html>", content)
