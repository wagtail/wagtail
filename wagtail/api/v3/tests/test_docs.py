from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base


class TestAPIDocsGating(TestV3Base, TestCase):
    def test_docs_served_by_default(self):
        response = self.client.get(reverse("wagtailapi_v3:openapi-json"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("wagtailapi_v3:openapi-view"))
        self.assertEqual(response.status_code, 200)

    @override_settings(WAGTAILAPI_DOCS_ENABLED=False)
    def test_docs_disabled_returns_404(self):
        response = self.client.get(reverse("wagtailapi_v3:openapi-json"))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("wagtailapi_v3:openapi-view"))
        self.assertEqual(response.status_code, 404)
