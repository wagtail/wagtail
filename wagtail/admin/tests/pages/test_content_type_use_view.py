import datetime
from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.http import urlencode
from openpyxl import load_workbook

from wagtail.models import GroupPagePermission, Page
from wagtail.test.testapp.models import EventPage
from wagtail.test.utils import WagtailTestUtils


class TestContentTypeUse(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.user = self.login()
        self.url = reverse("wagtailadmin_pages:type_use", args=("tests", "eventpage"))
        self.results_url = reverse(
            "wagtailadmin_pages:type_use_results", args=("tests", "eventpage")
        )
        self.christmas_page = EventPage.objects.get(title="Christmas")

    def test_with_no_permission(self):
        group = Group.objects.create(name="test group")
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.add(group)
        group.permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        # No GroupPagePermission created

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_with_minimal_permissions(self):
        group = Group.objects.create(name="test group")
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.add(group)
        group.permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            ),
        )
        GroupPagePermission.objects.create(
            group=group,
            page=Page.objects.first(),
            permission_type="change",
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_content_type_use(self):
        response = self.client.get(self.url)

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index.html")
        self.assertTemplateUsed(response, "wagtailadmin/pages/index_results.html")
        self.assertContains(response, "Christmas")

        # Links to 'delete' etc should include a 'next' URL parameter pointing back here
        delete_url = (
            reverse("wagtailadmin_pages:delete", args=(self.christmas_page.id,))
            + "?"
            + urlencode({"next": self.url})
        )
        self.assertContains(response, delete_url)
        self.assertContains(response, "data-bulk-action-select-all-checkbox")

        with self.assertNumQueries(33):
            self.client.get(self.url)

        soup = self.get_soup(response.content)
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
                    "Events",
                    "",
                    "Current page status: | live",
                    "Public",
                ],
                [
                    "",
                    "Saint Patrick (single event)",
                    "Events",
                    "",
                    "Current page status: | live",
                    "Private",
                ],
                [
                    "",
                    "Ameristralia Day",
                    "Events",
                    "",
                    "Current page status: | live",
                    "Public",
                ],
                [
                    "",
                    "Someone Else's Event",
                    "Events",
                    "",
                    "Current page status: | draft",
                    "Private",
                ],
                [
                    "",
                    "Steal underpants",
                    "Secret plans (simple page)",
                    "",
                    "Current page status: | live",
                    "Private",
                ],
                [
                    "",
                    "Tentative Unpublished Event",
                    "Events",
                    "",
                    "Current page status: | draft",
                    "Public",
                ],
            ],
        )

        # Should show an add button pointing to the generic choose parent view
        header_buttons = soup.select_one("#w-slim-header-buttons")
        self.assertIsNotNone(header_buttons)
        choose_parent_url = reverse(
            "wagtailadmin_pages:choose_parent", args=("tests", "eventpage")
        )
        add_button = header_buttons.select_one(f'a[href="{choose_parent_url}"]')
        self.assertIsNotNone(add_button)
        self.assertEqual(add_button.get_text(strip=True), "Add event page")

    def test_content_type_use_results(self):
        # Get the results view of event page use, with search and filter
        ameristralia_page = EventPage.objects.get(title="Ameristralia Day")
        user = get_user_model().objects.get(email="eventmoderator@example.com")
        response = self.client.get(
            self.results_url,
            data={"q": "Ameristralia", "owner": user.pk},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateNotUsed(response, "wagtailadmin/pages/index.html")
        self.assertTemplateUsed(response, "wagtailadmin/pages/index_results.html")
        self.assertContains(response, "Ameristralia Day")

        # Links to 'delete' etc should include a 'next' URL parameter pointing back
        # to the full view, not the results-only view
        full_view_url = reverse(
            "wagtailadmin_pages:type_use",
            args=("tests", "eventpage"),
        )
        delete_url = (
            reverse("wagtailadmin_pages:delete", args=(ameristralia_page.id,))
            + "?"
            + urlencode({"next": full_view_url})
        )
        self.assertContains(response, delete_url)
        self.assertContains(response, "data-bulk-action-select-all-checkbox")

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

        group = Group.objects.get(name="Event editors")
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.add(group)

        request_url = reverse(
            "wagtailadmin_pages:type_use", args=("tests", "eventpage")
        )
        response = self.client.get(request_url, {"q": "Christmas"})
        # The Event editors group should only see pages under the event index, which does not
        # include the independence day page
        page_ids = [result.pk for result in response.context["pages"]]
        self.assertCountEqual(page_ids, [EventPage.objects.get(title="Christmas").pk])

    @override_settings(WAGTAILADMIN_PAGE_SEARCH_FILTER_BY_PERMISSIONS=False)
    def test_search_filter_by_permission_disabled(self):
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

        group = Group.objects.get(name="Event editors")
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.add(group)

        request_url = reverse(
            "wagtailadmin_pages:type_use", args=("tests", "eventpage")
        )
        response = self.client.get(request_url, {"q": "Christmas"})
        # With the permission filter disabled, the Event editors group should see
        # both the Christmas page and the Christmas Island Independence Day page
        page_ids = [result.pk for result in response.context["pages"]]
        self.assertCountEqual(
            page_ids, [EventPage.objects.get(title="Christmas").pk, independence_day.pk]
        )

    def test_non_page_type(self):
        cases = [
            ("tests", "advert"),  # Not a page model
            ("tests", "modeldoesnotexist"),  # Non-existent model
        ]
        for app_label, model_name in cases:
            with self.subTest(app_label=app_label, model_name=model_name):
                request_url = reverse(
                    "wagtailadmin_pages:type_use",
                    args=(app_label, model_name),
                )
                response = self.client.get(request_url)
                self.assertEqual(response.status_code, 404)

    def test_order_by_audience(self):
        response = self.client.get(self.url, {"ordering": "audience"})
        self.assertEqual(response.status_code, 200)
        pages = response.context["object_list"]
        self.assertEqual(
            [page.audience for page in pages],
            ["private", "private", "private", "public", "public", "public"],
        )

    def test_filter(self):
        response = self.client.get(self.url, {"audience": "private"})
        self.assertEqual(response.status_code, 200)
        pages = response.context["object_list"]
        self.assertEqual(
            [page.audience for page in pages],
            ["private", "private", "private"],
        )
        soup = self.get_soup(response.content)
        title_th = soup.select_one("main table th.title")
        self.assertIsNotNone(title_th)
        # Not the explorable view, so no link to search the whole tree as it's
        # already querying the whole tree
        search_whole_tree_url = f"{self.url}?audience=private&search_all=1"
        search_whole_tree_link = title_th.select_one(
            f'a[href="{search_whole_tree_url}"]'
        )
        self.assertIsNone(search_whole_tree_link)

    def test_filter_results(self):
        response = self.client.get(self.results_url, {"audience": "private"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index_results.html")
        pages = response.context["object_list"]
        self.assertEqual(
            [page.audience for page in pages],
            ["private", "private", "private"],
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
        # from the register_page_header_buttons hook are not shown as this is not
        # the explorable index view so there's no parent page to associate with
        self.assertEqual(
            {
                f"{self.results_url}?audience=private&export=xlsx",
                f"{self.results_url}?audience=private&export=csv",
            },
            {btn["href"] for btn in buttons},
        )
        self.assertEqual(len(buttons), 2)
        self.assertEqual(
            [button.text.strip() for button in buttons],
            ["Download XLSX", "Download CSV"],
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
        self.assertIsNone(search_whole_tree_link)

    def test_default_order_by_date_from(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        pages = response.context["object_list"]
        self.assertEqual(
            [str(page.date_from) for page in pages],
            [
                "2014-12-25",
                "2014-12-25",
                "2015-04-22",
                "2015-07-04",
                "2015-07-04",
                "2015-07-04",
            ],
        )

    def test_render_export_buttons(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        dropdown = soup.select_one(
            "#w-slim-header-buttons [data-controller='w-dropdown']"
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
                    "12,Steal underpants,private,2015-07-04",
                    "5,Tentative Unpublished Event,public,2015-07-04",
                ],
            ],
            [
                {"export": "csv", "audience": "private", "ordering": "title"},
                [
                    "Pk,Title,Audience,Start date",
                    "13,Saint Patrick,private,2014-12-25",
                    "6,Someone Else's Event,private,2015-07-04",
                    "12,Steal underpants,private,2015-07-04",
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
                    [12, "Steal underpants", "private", datetime.date(2015, 7, 4)],
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
                    [12, "Steal underpants", "private", datetime.date(2015, 7, 4)],
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
        root_page = Page.objects.get(pk=2)
        for page in pages:
            root_page.add_child(instance=page)
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
            ["Page 1 of 3", "Previous", "1", "2", "3", "Next", "26 event pages"],
        )
