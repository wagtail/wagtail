import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer

from wagtail.admin.api.views import PagesAdminAPIViewSet
from wagtail.test.utils import WagtailTestUtils


class TestPagesAdminAPIRendererClasses(WagtailTestUtils, TestCase):
    """Test that PagesAdminAPIViewSet renderer behavior works correctly."""

    def setUp(self):
        self.user = self.login()

    def test_renderer_classes_with_rest_framework_installed(self):
        """Test that both JSONRenderer and BrowsableAPIRenderer are included when rest_framework is installed."""
        renderer_classes = PagesAdminAPIViewSet.renderer_classes
        # Should have both renderers when rest_framework is installed
        self.assertEqual(renderer_classes, [JSONRenderer, BrowsableAPIRenderer])

    @patch("wagtail.api.v2.views.apps.is_installed")
    def test_renderer_classes_without_rest_framework(self, mock_is_installed):
        """Test that only JSONRenderer is included when rest_framework is not installed."""

        # Mock rest_framework as not installed
        def mock_installed(app):
            return app != "rest_framework"

        mock_is_installed.side_effect = mock_installed

        renderer_classes = PagesAdminAPIViewSet.renderer_classes
        self.assertEqual(renderer_classes, [JSONRenderer])

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
