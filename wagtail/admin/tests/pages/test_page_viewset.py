from django.test import TestCase
from django.urls import reverse

from wagtail.test.testapp.models import EventIndex
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils


class TestCustomExplorableIndexView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    fixtures = ["test.json"]
    base_breadcrumb_items = [
        {"url": reverse("wagtailadmin_explore_root"), "label": "Root"}
    ]

    def setUp(self):
        self.user = self.login()

    def test_get(self):
        event_index_page = EventIndex.objects.first()
        parent = event_index_page.get_parent()
        url = reverse("wagtailadmin_explore", args=[event_index_page.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index.html")
        self.assertBreadcrumbsItemsRendered(
            [
                {
                    "url": reverse("wagtailadmin_explore", args=[parent.pk]),
                    "label": str(parent),
                },
                {"url": url, "label": "Events"},
            ],
            response.content,
        )

        soup = self.get_soup(response.content)

        breadcrumbs_icon = soup.select_one(".w-breadcrumbs__icon")
        self.assertIsNotNone(breadcrumbs_icon)
        use = breadcrumbs_icon.select_one("use")
        self.assertIsNotNone(use)
        self.assertEqual(use["href"], "#icon-calendar")

        table = soup.select_one("main table")
        for dropdown in table.select("[data-controller='w-dropdown']"):
            dropdown.extract()
        trs = table.select("tbody tr")
        tds = [
            [td.get_text(strip=True, separator=" | ") for td in tr.select("td")]
            for tr in trs
        ]
        self.assertEqual(
            tds,
            [
                [
                    "",
                    "Christmas",
                    "",
                    "Event page",
                    "Current page status: | live",
                    "public",
                    "",
                ],
                [
                    "",
                    "Tentative Unpublished Event",
                    "",
                    "Event page",
                    "Current page status: | draft",
                    "public",
                    "",
                ],
                [
                    "",
                    "Someone Else's Event",
                    "",
                    "Event page",
                    "Current page status: | draft",
                    "private",
                    "",
                ],
                [
                    "",
                    "Ameristralia Day",
                    "",
                    "Event page",
                    "Current page status: | live",
                    "public",
                    "",
                ],
                [
                    "",
                    "Saint Patrick (single event)",
                    "",
                    "Single event page",
                    "Current page status: | live",
                    "private",
                    "",
                ],
                [
                    "",
                    "Businessy events",
                    "",
                    "Business index",
                    "Current page status: | draft",
                    "",
                    "",
                ],
            ],
        )
