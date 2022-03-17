from django.test import TestCase
from django.urls import reverse

from wagtail.test.utils import WagtailTestUtils


class TestStyleGuide(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def test_styleguide(self):
        response = self.client.get(reverse("wagtailstyleguide"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailstyleguide/base.html")
