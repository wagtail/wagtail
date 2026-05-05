import datetime
from io import BytesIO
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.test import SimpleTestCase, TestCase
from django.test.utils import isolate_apps
from django.urls import reverse
from openpyxl import load_workbook

from wagtail.admin.viewsets.pages import PageViewSet, page_viewset_registry
from wagtail.coreutils import get_dummy_request
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


class TestPageViewSetRegistry(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def test_as_view(self):
        cases = [
            (
                "edit",
                {"page_id_kwarg": "page_id"},
                {"page_id": EventPage.objects.first().pk},
            ),
            (
                "index",
                {"parent_page_id_kwarg": "parent_page_id"},
                {"parent_page_id": EventIndex.objects.first().pk},
            ),
            (
                "content_type_use",
                {
                    "app_label_kwarg": "content_type_app_name",
                    "model_name_kwarg": "content_type_model_name",
                },
                {
                    "content_type_app_name": "tests",
                    "content_type_model_name": "eventpage",
                },
            ),
        ]
        request = get_dummy_request()
        request.user = self.login()
        for view_name, kwargs_names, kwargs_values in cases:
            with self.subTest(view_name=view_name):
                view = page_viewset_registry.as_view(view_name, **kwargs_names)
                self.assertIs(callable(view), True)
                response = view(request, **kwargs_values)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.headers.get("X-Wagtail-ViewSet"),
                    "EventPageViewSet",
                )

    def test_as_view_with_incorrect_kwargs(self):
        kwargs_cases = [
            {"app_label_kwarg": "app_label"},
            {"model_name_kwarg": "model_name"},
            {},
        ]
        for kwargs in kwargs_cases:
            with self.subTest(kwargs=kwargs):
                # Incorrect kwargs combination should be caught immediately and
                # produce a clear error message.
                with self.assertRaisesMessage(
                    ImproperlyConfigured,
                    "PageViewSetRegistry.as_view('index', …) requires one of "
                    "the following combinations of kwargs:\n"
                    "- page_id_kwarg,\n"
                    "- parent_page_id_kwarg, or\n"
                    "- app_label_kwarg and model_name_kwarg.",
                ):
                    page_viewset_registry.as_view("index", **kwargs)

    def test_as_view_with_nonexistent_view_name(self):
        view = page_viewset_registry.as_view("willneverexist", page_id_kwarg="pk")
        request = get_dummy_request()
        # Resolving the view name happens at request time since we need to look
        # up the viewset first. This means the error message will be user-facing,
        # use a Http404 so it can be handled gracefully.
        with self.assertRaises(Http404):
            view(request, pk=2)


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
        soup = self.get_soup(response.content)
        title_th = soup.select_one("main table th.title")
        self.assertIsNotNone(title_th)
        search_whole_tree_url = f"{self.url}?audience=private&search_all=1"
        search_whole_tree_link = title_th.select_one(
            f'a[href="{search_whole_tree_url}"]'
        )
        self.assertIsNotNone(search_whole_tree_link)
        self.assertHTMLEqual(
            search_whole_tree_link.extract().decode_contents(),
            "Search the whole site",
        )
        self.assertEqual(
            title_th.get_text(strip=True, separator=" | "),
            "Title | 1-2 of 2 event pages in ' | Events | '.",
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
        soup = self.get_soup(response.content)
        header_buttons_fragment = soup.select_one(
            'template[data-controller="w-teleport"]'
            '[data-w-teleport-target-value="#w-slim-header-buttons"]'
            '[data-w-teleport-mode-value="innerHTML"]'
        )
        self.assertIsNotNone(header_buttons_fragment)
        buttons = header_buttons_fragment.select('[data-w-dropdown-target="content"] a')
        # Check that download links preserve the current filters, and buttons
        # from the register_page_header_buttons hook are also shown
        self.assertLess(
            {
                f"{self.results_url}?audience=private&export=xlsx",
                f"{self.results_url}?audience=private&export=csv",
            },
            {btn["href"] for btn in buttons},
        )
        self.assertEqual(len(buttons), 9)
        self.assertEqual(
            [button.text.strip() for button in buttons],
            [
                "Edit",
                "Move",
                "Copy",
                "Delete",
                "Unpublish",
                "History",
                "Sort menu order",
                "Download XLSX",
                "Download CSV",
            ],
        )

    def test_search_filter(self):
        response = self.client.get(self.url, {"q": "event", "audience": "private"})
        self.assertEqual(response.status_code, 200)
        pages = response.context["object_list"]
        self.assertEqual({page.title for page in pages}, {"Someone Else's Event"})
        self.assertEqual([page.audience for page in pages], ["private"])
        soup = self.get_soup(response.content)
        title_th = soup.select_one("main table th.title")
        self.assertIsNotNone(title_th)
        search_whole_tree_url = f"{self.url}?q=event&audience=private&search_all=1"
        search_whole_tree_link = title_th.select_one(
            f'a[href="{search_whole_tree_url}"]'
        )
        self.assertIsNotNone(search_whole_tree_link)
        self.assertHTMLEqual(
            search_whole_tree_link.extract().decode_contents(),
            "Search the whole site",
        )
        self.assertEqual(
            title_th.get_text(strip=True, separator=" | "),
            "Title | 1-1 of 1 event page in ' | Events | '.",
        )

    def test_search_filter_whole_tree(self):
        root_page = Page.objects.get(pk=2)
        new_page = EventPage(
            title="Nice private event",
            date_from="2026-04-01",
            location="somewhere else on the site",
            cost="nada",
            audience="private",
        )
        root_page.add_child(instance=new_page)
        response = self.client.get(
            self.url,
            {"q": "event", "audience": "private", "search_all": "1"},
        )
        self.assertEqual(response.status_code, 200)
        pages = response.context["object_list"]
        self.assertEqual(
            {page.title for page in pages},
            {"Nice private event", "Someone Else's Event"},
        )
        self.assertEqual([page.audience for page in pages], ["private", "private"])
        soup = self.get_soup(response.content)
        title_th = soup.select_one("main table th.title")
        self.assertIsNotNone(title_th)
        search_in_parent_url = f"{self.url}?q=event&audience=private"
        search_parent_link = title_th.select_one(f'a[href="{search_in_parent_url}"]')
        self.assertIsNotNone(search_parent_link)
        self.assertHTMLEqual(
            search_parent_link.extract().decode_contents(),
            "Search in '<span class=\"w-title-ellipsis\">Events</span>'",
        )
        self.assertEqual(
            title_th.get_text(strip=True, separator=" | "),
            "Title | 1-2 of 2 event pages across entire site.",
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

    def test_render_export_buttons(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        dropdown = soup.select_one(
            "nav#w-slim-header-buttons [data-controller='w-dropdown']"
        )
        self.assertIsNotNone(dropdown)
        expected = [
            (f"{self.url}?export=csv", "Download CSV"),
            (f"{self.url}?export=xlsx", "Download XLSX"),
        ]
        for url, label in expected:
            button = dropdown.select_one(f'a[href="{url}"]')
            self.assertIsNotNone(button)
            self.assertEqual(button.get_text(strip=True), label)

    def test_csv_export(self):
        cases = [
            [
                {"export": "csv", "ordering": "title"},
                [
                    "Pk,Title,Audience,Start date",
                    "9,Ameristralia Day,public,2015-04-22",
                    "4,Christmas,public,2014-12-25",
                    "13,Saint Patrick,private,2014-12-25",
                    "6,Someone Else's Event,private,2015-07-04",
                    "5,Tentative Unpublished Event,public,2015-07-04",
                ],
            ],
            [
                {"export": "csv", "audience": "private", "ordering": "title"},
                [
                    "Pk,Title,Audience,Start date",
                    "13,Saint Patrick,private,2014-12-25",
                    "6,Someone Else's Event,private,2015-07-04",
                ],
            ],
        ]
        for params, results in cases:
            with self.subTest(params=params):
                response = self.client.get(self.url, params)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response["Content-Disposition"],
                    'attachment; filename="tests_eventpage.csv"',
                )
                data_lines = response.getvalue().decode().strip().split("\r\n")
                self.assertEqual(data_lines, results)

    def test_xlsx_export(self):
        cases = [
            [
                {"export": "xlsx", "ordering": "title"},
                [
                    ["Pk", "Title", "Audience", "Start date"],
                    [9, "Ameristralia Day", "public", datetime.date(2015, 4, 22)],
                    [4, "Christmas", "public", datetime.date(2014, 12, 25)],
                    [13, "Saint Patrick", "private", datetime.date(2014, 12, 25)],
                    [6, "Someone Else's Event", "private", datetime.date(2015, 7, 4)],
                    [
                        5,
                        "Tentative Unpublished Event",
                        "public",
                        datetime.date(2015, 7, 4),
                    ],
                ],
            ],
            [
                {"export": "xlsx", "audience": "private", "ordering": "title"},
                [
                    ["Pk", "Title", "Audience", "Start date"],
                    [13, "Saint Patrick", "private", datetime.date(2014, 12, 25)],
                    [6, "Someone Else's Event", "private", datetime.date(2015, 7, 4)],
                ],
            ],
        ]
        for params, results in cases:
            with self.subTest(params=params):
                response = self.client.get(self.url, params)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response["Content-Disposition"],
                    'attachment; filename="tests_eventpage.xlsx"',
                )
                workbook_data = response.getvalue()
                worksheet = load_workbook(filename=BytesIO(workbook_data)).active
                data_cells = [[cell.value for cell in row] for row in worksheet.rows]
                self.assertEqual(data_cells, results)

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


class TestCustomViews(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.user = self.login()

    @classmethod
    def setUpTestData(cls):
        cls.event_index_page = EventIndex.objects.first()
        cls.event_page = EventPage.objects.first()
        cls.old_revision = cls.event_page.save_revision()
        cls.new_revision = cls.event_page.save_revision()

    def test_views(self):
        urls = [
            reverse(
                "wagtailadmin_explore",
                args=[self.event_index_page.id],
            ),
            reverse(
                "wagtailadmin_explore_results",
                args=[self.event_index_page.id],
            ),
            reverse(
                "wagtailadmin_pages:add",
                args=["tests", "eventpage", self.event_index_page.id],
            ),
            reverse(
                "wagtailadmin_pages:choose_parent",
                args=["tests", "eventpage"],
            ),
            reverse(
                "wagtailadmin_pages:edit",
                args=[self.event_page.id],
            ),
            reverse(
                "wagtailadmin_pages:preview_on_add",
                args=["tests", "eventpage", self.event_index_page.id],
            ),
            reverse(
                "wagtailadmin_pages:preview_on_edit",
                args=[self.event_page.id],
            ),
            reverse(
                "wagtailadmin_pages:revisions_revert",
                args=[self.event_page.id, self.old_revision.pk],
            ),
            reverse(
                "wagtailadmin_pages:type_use",
                args=["tests", "eventpage"],
            ),
            reverse(
                "wagtailadmin_pages:type_use_results",
                args=["tests", "eventpage"],
            ),
            reverse(
                "wagtailadmin_pages:usage",
                args=[self.event_page.id],
            ),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.headers.get("X-Wagtail-ViewSet"),
                    "EventPageViewSet",
                )
