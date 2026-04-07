from unittest import mock

from django.test import SimpleTestCase, TestCase
from django.test.utils import isolate_apps
from django.urls import reverse

from wagtail.admin.viewsets.pages import PageViewSet
from wagtail.models import Page
from wagtail.test.testapp.models import (
    BusinessChild,
    BusinessSubIndex,
    EventIndex,
    EventPage,
    SimpleChildPage,
    SimplePage,
    SimpleParentPage,
)
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils


class TestPageViewSet(SimpleTestCase):
    def test_default_parent_models(self):
        self.assertEqual(PageViewSet(model=SimplePage).parent_models, [])

    def test_default_parent_models_with_type_restrictions(self):
        # Simple one-to-one mapping
        self.assertEqual(
            PageViewSet(model=SimpleChildPage).parent_models,
            [SimpleParentPage],
        )

        # BusinessChild can exist under BusinessIndex and BusinessSubIndex.
        # BusinessIndex can contain BusinessChild or BusinessSubIndex, and
        # the latter is not a subclass of the former.
        # BusinessSubIndex can only contain BusinessChild.
        # Associating the viewset with BusinessIndex would prevent
        # BusinessSubIndex from being shown when listing the children of
        # BusinessIndex (as we would only query BusinessChild pages).
        # Therefore, we only associate the viewset with BusinessSubIndex.
        self.assertEqual(
            PageViewSet(model=BusinessChild).parent_models,
            [BusinessSubIndex],
        )

    @isolate_apps("wagtail.test.testapp", "wagtail", kwarg_name="apps")
    def test_multiple_default_parent_models(self, apps):
        # We are not under the testapp directory, so explicitly define app_label
        class TestsMeta:
            app_label = "tests"

        class BaseChild(Page):
            parent_page_types = ["tests.BaseParent", "tests.BaseAndSpecificParent"]
            Meta = TestsMeta

        class SpecificChild(BaseChild):
            parent_page_types = ["tests.SpecificParent", "tests.BaseAndSpecificParent"]
            Meta = TestsMeta

        class BaseParent(Page):
            subpage_types = [BaseChild]
            Meta = TestsMeta

        class BaseAndSpecificParent(Page):
            subpage_types = [BaseChild, SpecificChild]
            Meta = TestsMeta

        class SpecificParent(Page):
            subpage_types = [SpecificChild]
            Meta = TestsMeta

        # Patch the registry used for resolving model strings with the isolated version
        with mock.patch("wagtail.coreutils.apps", apps):
            self.assertEqual(
                PageViewSet(model=BaseChild).parent_models,
                [
                    # BaseParent can only have BaseChild children, so it is included.
                    BaseParent,
                    # BaseAndSpecificParent can have both BaseChild and SpecificChild
                    # children. SpecificChild pages are also BaseChild pages and thus
                    # can be queried as BaseChild, so it is okay to use this viewset
                    # for BaseAndSpecificParent.
                    BaseAndSpecificParent,
                    # SpecificParent does not allow BaseChild children.
                ],
            )
            self.assertEqual(
                PageViewSet(model=SpecificChild).parent_models,
                [
                    # SpecificChild can exist under SpecificParent and
                    # SpecificParent only allows SpecificChild to exist under it.
                    SpecificParent
                    # Even though SpecificChild can exist under BaseAndSpecificParent,
                    # and BaseAndSpecificParent allows SpecificChild to exist under it,
                    # associating BaseAndSpecificParent here would prevent BaseChild
                    # pages (that are not SpecificChild) from being displayed, so
                    # we do not include it by default.
                ],
            )


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
                    "Public",
                    "",
                ],
                [
                    "",
                    "Saint Patrick (single event)",
                    "",
                    "Single event page",
                    "Current page status: | live",
                    "Private",
                    "",
                ],
                [
                    "",
                    "Ameristralia Day",
                    "",
                    "Event page",
                    "Current page status: | live",
                    "Public",
                    "",
                ],
                [
                    "",
                    "Someone Else's Event",
                    "",
                    "Event page",
                    "Current page status: | draft",
                    "Private",
                    "",
                ],
                [
                    "",
                    "Tentative Unpublished Event",
                    "",
                    "Event page",
                    "Current page status: | draft",
                    "Public",
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

    def test_default_order_by_date_from(self):
        new_page = EventPage(
            title="New Years 2025",
            date_from="2015-01-01",
            audience="public",
            location="Somewhere",
            cost="free",
        )
        self.event_index_page.add_child(instance=new_page)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        pages = response.context["object_list"]
        self.assertEqual(
            [str(page.date_from) for page in pages],
            [
                "2014-12-25",
                "2014-12-25",
                "2015-01-01",
                "2015-04-22",
                "2015-07-04",
                "2015-07-04",
            ],
        )

    def test_list_per_page(self):
        pages = [
            EventPage(
                title=f"Event {i}",
                date_from=f"2015-01-{i}",
                audience="public",
                location="Somewhere",
                cost=f"£{i}",
            )
            for i in range(1, 21)
        ]
        for page in pages:
            self.event_index_page.add_child(instance=page)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["object_list"]), 10)
        soup = self.get_soup(response.content)
        pagination = (
            soup.select_one("nav.pagination")
            .get_text(strip=True, separator="|")
            .split("|")
        )
        self.assertEqual(
            pagination,
            ["Page 1 of 3", "Previous", "1", "2", "3", "Next", "25 event pages"],
        )
