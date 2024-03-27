from django.test import TestCase
from django.urls import reverse

from wagtail.models import Page
from wagtail.test.utils.wagtail_tests import WagtailTestUtils


class TestParentPageChooserView(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        super().setUp()
        self.login()

        self.view_url = reverse("event_pages:choose_parent")

    def test_get_page_parent_chooser(self):
        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/choose_parent.html")

    def test_parent_chooser_redirect(self):
        parent_page = Page.objects.first()
        form_data = {
            "parent_page": parent_page.pk,
        }

        response = self.client.post(self.view_url, form_data)
        self.assertRedirects(
            response,
            reverse(
                "wagtailadmin_pages:add", args=("tests", "eventpage", parent_page.pk)
            ),
        )

        # Test another parent to make sure everything is working as intended
        another_parent = parent_page.get_first_child()
        form_data["parent_page"] = another_parent.pk

        response = self.client.post(self.view_url, form_data)
        self.assertRedirects(
            response,
            reverse(
                "wagtailadmin_pages:add", args=("tests", "eventpage", another_parent.pk)
            ),
        )

    def test_no_parent_selected(self):
        error_html = """<p class="error-message">This field is required.</p>"""

        response = self.client.post(self.view_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, error_html, html=True)

    def test_proper_breadcrumb(self):
        listing_url = reverse("event_pages:index")
        expanded_breadcrumb = (
            """<a class="w-flex w-items-center w-text-text-label w-pr-0.5 w-text-14 w-no-underline w-outline-offset-inside w-border-b w-border-b-2 w-border-transparent w-box-content hover:w-border-current hover:w-text-text-label" href="%s">Event pages</a>"""
            % listing_url
        )
        collapsed_breadcrumb = """<span class="w-breadcrumbs__sublabel w-font-normal w-hidden w-ml-2.5">Event page</span>"""

        response = self.client.get(self.view_url)
        self.assertContains(response, expanded_breadcrumb, html=True)
        self.assertContains(response, collapsed_breadcrumb, html=True)
