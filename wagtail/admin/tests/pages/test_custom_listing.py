from django.test import TestCase
from django.urls import reverse

from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils


class TestCustomListing(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.user = self.login()

    def test_get(self):
        response = self.client.get("/admin/event_pages/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index.html")
        self.assertContains(response, "Event pages")
        self.assertContains(response, "Christmas")
        self.assertContains(response, "Saint Patrick")
        self.assertNotContains(response, "Welcome to the Wagtail test site!")
        self.assertBreadcrumbsItemsRendered(
            [{"url": "", "label": "Event pages"}],
            response.content,
        )
        soup = self.get_soup(response.content)
        breadcrumbs_icon = soup.select_one(".w-breadcrumbs__icon")
        self.assertIsNotNone(breadcrumbs_icon)
        use = breadcrumbs_icon.select_one("use")
        self.assertIsNotNone(use)
        self.assertEqual(use["href"], "#icon-calendar")

    def test_filter(self):
        response = self.client.get("/admin/event_pages/", {"audience": "private"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index.html")
        self.assertContains(response, "Event pages")
        self.assertNotContains(response, "Christmas")
        self.assertContains(response, "Saint Patrick")

        # Should render bulk action buttons
        soup = self.get_soup(response.content)
        bulk_actions = soup.select("[data-bulk-action-button]")
        self.assertTrue(bulk_actions)
        # 'next' parameter is constructed client-side later based on filters state
        for action in bulk_actions:
            self.assertNotIn("next=", action["href"])

    def test_filter_index_results(self):
        results_url = reverse("event_pages:index_results")
        filtered_url = f"{results_url}?audience=private"
        response = self.client.get(filtered_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index_results.html")
        soup = self.get_soup(response.content)
        tbody = soup.select_one("tbody")
        self.assertIsNotNone(tbody)
        self.assertIn("Saint Patrick", tbody.text)
        self.assertNotIn("Christmas", tbody.text)
        active_filters = soup.select("[data-w-active-filter-id]")
        self.assertEqual(len(active_filters), 1)
        self.assertEqual(
            active_filters[0].get_text(separator=" ", strip=True),
            "Audience: Private",
        )
        header_buttons_fragment = soup.select_one(
            'template[data-controller="w-teleport"]'
            '[data-w-teleport-target-value="#w-slim-header-buttons"]'
            '[data-w-teleport-mode-value="innerHTML"]'
        )
        self.assertIsNotNone(header_buttons_fragment)
        download_buttons = header_buttons_fragment.select(
            '[data-w-dropdown-target="content"] a'
        )
        self.assertEqual(len(download_buttons), 2)
        # Check that download links preserve the current filters
        self.assertEqual(
            {btn["href"] for btn in download_buttons},
            {
                f"{filtered_url}&export=xlsx",
                f"{filtered_url}&export=csv",
            },
        )
