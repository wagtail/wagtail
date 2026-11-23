import swapper
from django.test import TestCase
from django.test.utils import override_script_prefix
from django.urls import reverse
from django.utils.http import urlencode

from wagtail.test.testapp.models import EventPage, SimplePage
from wagtail.test.utils import Page, WagtailTestUtils

page_app, page_model = swapper.split(
    swapper.get_model_name("wagtailcore", "Page").lower()
)


class TestBulkActionDispatcher(WagtailTestUtils, TestCase):
    def setUp(self):
        # Login
        self.user = self.login()

    def test_bulk_action_invalid_action(self):
        url = reverse(
            "wagtail_bulk_action",
            args=(
                page_app,
                page_model,
                "ships",
            ),
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_bulk_action_invalid_model(self):
        url = reverse(
            "wagtail_bulk_action",
            args=(
                "doesnotexist",
                "doesnotexist",
                "doesnotexist",
            ),
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class TestBulkActionSelectAllInListing(WagtailTestUtils, TestCase):
    """
    "Select all in listing" acts on the items of the listing given in
    ``listing_url``, with its search and filters applied.
    """

    def setUp(self):
        self.user = self.login()
        self.root_page = Page.objects.get(id=2)
        self.parent = self.root_page.add_child(
            instance=SimplePage(title="Parent", slug="parent", content="parent")
        )
        self.child = self.parent.add_child(
            instance=SimplePage(title="Child", slug="child", content="child")
        )
        self.leaf = self.root_page.add_child(
            instance=SimplePage(title="Leaf", slug="leaf", content="leaf")
        )
        self.event = self.root_page.add_child(
            instance=EventPage(
                title="Event",
                slug="event",
                audience="private",
                date_from="2024-12-01",
                location="Christmas Island",
                cost="Free",
            )
        )
        self.explore_url = reverse("wagtailadmin_explore", args=[self.root_page.id])

    def get_action_url(self, action, listing_url):
        return (
            reverse("wagtail_bulk_action", args=(page_app, page_model, action))
            + "?"
            + urlencode({"id": "all", "listing_url": listing_url})
        )

    def get_page_ids(self, response):
        self.assertEqual(response.status_code, 200)
        return {item["item"].pk for item in response.context["items"]}

    def get_listed_page_ids(self, listing_url):
        response = self.client.get(self.get_action_url("delete", listing_url))
        return self.get_page_ids(response)

    def test_explorer(self):
        self.assertEqual(
            self.get_listed_page_ids(self.explore_url),
            {self.parent.pk, self.leaf.pk, self.event.pk},
        )

    def test_explorer_with_filter(self):
        listing_url = self.explore_url + "?has_child_pages=true"
        self.assertEqual(self.get_listed_page_ids(listing_url), {self.parent.pk})

        response = self.client.post(self.get_action_url("delete", listing_url))
        self.assertEqual(response.status_code, 302)
        # Only the page in the filtered listing (and its descendants) is deleted
        self.assertFalse(
            Page.objects.filter(pk__in=[self.parent.pk, self.child.pk]).exists()
        )
        self.assertTrue(Page.objects.filter(pk=self.leaf.pk).exists())
        self.assertTrue(Page.objects.filter(pk=self.event.pk).exists())

    def test_explorer_with_search(self):
        # Searching in the explorer looks through all descendants
        listing_url = self.explore_url + "?q=child"
        self.assertEqual(self.get_listed_page_ids(listing_url), {self.child.pk})

    def test_page_type_usage_listing(self):
        listing_url = reverse(
            "wagtailadmin_pages:type_use", args=("tests", "eventpage")
        )
        self.assertEqual(self.get_listed_page_ids(listing_url), {self.event.pk})

    def test_custom_page_listing_with_filter(self):
        self.root_page.add_child(
            instance=EventPage(
                title="Public event",
                slug="public-event",
                audience="public",
                date_from="2024-12-01",
                location="Christmas Island",
                cost="Free",
            )
        )
        listing_url = reverse("event_pages:index") + "?audience=private"
        self.assertEqual(self.get_listed_page_ids(listing_url), {self.event.pk})

    def test_page_search_with_content_type(self):
        listing_url = (
            reverse("wagtailadmin_pages:search")
            + "?"
            + urlencode({"content_type": "tests.eventpage"})
        )
        self.assertEqual(self.get_listed_page_ids(listing_url), {self.event.pk})

    def test_listing_url_with_script_prefix(self):
        url = self.get_action_url(
            "delete", "/cms" + self.explore_url + "?has_child_pages=true"
        )
        with override_script_prefix("/cms/"):
            response = self.client.get(url, SCRIPT_NAME="/cms")
        self.assertEqual(self.get_page_ids(response), {self.parent.pk})

    def test_without_listing_url(self):
        url = (
            reverse("wagtail_bulk_action", args=(page_app, page_model, "delete"))
            + "?id=all"
        )
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertEqual(Page.objects.filter(depth__gt=1).count(), 5)

    def test_listing_url_not_a_page_listing(self):
        for listing_url in (
            "/does-not-exist/",
            reverse("wagtailadmin_home"),
            reverse("wagtailimages:index"),
        ):
            with self.subTest(listing_url=listing_url):
                response = self.client.get(self.get_action_url("delete", listing_url))
                self.assertEqual(response.status_code, 404)
