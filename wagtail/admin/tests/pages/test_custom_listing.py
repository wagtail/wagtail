from django.test import TestCase

from wagtail.test.utils import WagtailTestUtils


class TestCustomListing(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def test_get(self):
        self.login()
        response = self.client.get("/admin/event_pages/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index.html")
        self.assertContains(response, "Event pages")
        self.assertContains(response, "Christmas")
        self.assertContains(response, "Saint Patrick")
        self.assertNotContains(response, "Welcome to the Wagtail test site!")

    def test_filter(self):
        self.login()
        response = self.client.get("/admin/event_pages/", {"audience": "private"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index.html")
        self.assertContains(response, "Event pages")
        self.assertNotContains(response, "Christmas")
        self.assertContains(response, "Saint Patrick")
