from django.contrib.auth.models import Group
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from wagtail.models import Page
from wagtail.test.testapp.models import EventPage
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

    def test_search(self):
        home = Page.objects.get(url_path="/home/")
        independence_day = EventPage(
            title="Christmas Island Independence Day",
            slug="independence-day",
            audience="public",
            date_from="2024-12-01",
            location="Christmas Island",
            cost="Free",
            live=True,
        )
        home.add_child(instance=independence_day)

        response = self.client.get("/admin/event_pages/", {"q": "Christmas"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index.html")
        page_ids = [result.pk for result in response.context["pages"]]
        self.assertCountEqual(
            page_ids, [independence_day.pk, EventPage.objects.get(title="Christmas").pk]
        )

    def test_search_filter_by_permission(self):
        home = Page.objects.get(url_path="/home/")
        independence_day = EventPage(
            title="Christmas Island Independence Day",
            slug="independence-day",
            audience="public",
            date_from="2024-12-01",
            location="Christmas Island",
            cost="Free",
            live=True,
        )
        home.add_child(instance=independence_day)

        # make self.user a member of "Event editors" instead of a superuser -
        # this group has access to the "Christmas" page but not the "Christmas Island Independence Day" page
        # (as the latter is not within the Events index)
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.add(Group.objects.get(name="Event editors"))

        response = self.client.get("/admin/event_pages/", {"q": "Christmas"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index.html")
        page_ids = [result.pk for result in response.context["pages"]]
        self.assertCountEqual(page_ids, [EventPage.objects.get(title="Christmas").pk])

    @override_settings(WAGTAILADMIN_PAGE_SEARCH_FILTER_BY_PERMISSIONS=False)
    def test_search_disable_filter_by_permission(self):
        home = Page.objects.get(url_path="/home/")
        independence_day = EventPage(
            title="Christmas Island Independence Day",
            slug="independence-day",
            audience="public",
            date_from="2024-12-01",
            location="Christmas Island",
            cost="Free",
            live=True,
        )
        home.add_child(instance=independence_day)

        # make self.user a member of "Event editors" instead of a superuser -
        # this group has access to the "Christmas" page but not the "Christmas Island Independence Day" page
        # (as the latter is not within the Events index)
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.add(Group.objects.get(name="Event editors"))

        response = self.client.get("/admin/event_pages/", {"q": "Christmas"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index.html")
        page_ids = [result.pk for result in response.context["pages"]]
        self.assertCountEqual(
            page_ids, [EventPage.objects.get(title="Christmas").pk, independence_day.pk]
        )
