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

    @classmethod
    def setUpTestData(cls):
        cls.event_index_page = EventIndex.objects.first()
        cls.parent = cls.event_index_page.get_parent()
        cls.url = reverse("wagtailadmin_explore", args=[cls.event_index_page.id])
        cls.results_url = reverse(
            "wagtailadmin_explore_results",
            args=[cls.event_index_page.id],
        )

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index.html")
        self.assertBreadcrumbsItemsRendered(
            [
                {
                    "url": reverse("wagtailadmin_explore", args=[self.parent.pk]),
                    "label": str(self.parent),
                },
                {"url": self.url, "label": "Events"},
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
            ],
        )

    def test_order_by_audience(self):
        response = self.client.get(self.url, {"ordering": "audience"})
        self.assertEqual(response.status_code, 200)
        pages = response.context["object_list"]
        self.assertEqual(
            [page.audience for page in pages],
            ["private", "private", "public", "public", "public"],
        )

    def test_filter(self):
        response = self.client.get(self.url, {"audience": "private"})
        self.assertEqual(response.status_code, 200)
        pages = response.context["object_list"]
        self.assertEqual(
            [page.audience for page in pages],
            ["private", "private"],
        )

    def test_filter_results(self):
        response = self.client.get(self.results_url, {"audience": "private"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index_results.html")
        pages = response.context["object_list"]
        self.assertEqual(
            [page.audience for page in pages],
            ["private", "private"],
        )
