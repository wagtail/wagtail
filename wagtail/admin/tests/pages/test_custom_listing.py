from django.test import TestCase
from django.urls import reverse

from wagtail.models import Page
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

    def test_get_page_parent_chooser(self):
        self.login()
        response = self.client.get("/admin/event_pages/choose_parent/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/choose_parent.html")

    def test_parent_chooser_redirect(self):
        parent_page = Page.objects.first()
        form_data = {
            "parent_page": parent_page.pk,
        }

        self.login()
        response = self.client.post("/admin/event_pages/choose_parent/", form_data)
        self.assertRedirects(
            response,
            reverse(
                "wagtailadmin_pages:add", args=("tests", "eventpage", parent_page.pk)
            ),
        )

        # Test another parent to make sure everything is working as needed
        another_parent = parent_page.get_first_child()
        form_data["parent_page"] = another_parent.pk
        
        response = self.client.post("/admin/event_pages/choose_parent/", form_data)
        self.assertRedirects(
            response,
            reverse(
                "wagtailadmin_pages:add", args=("tests", "eventpage", another_parent.pk)
            ),
        )
