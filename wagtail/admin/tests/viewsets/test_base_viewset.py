import json

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from wagtail.test.utils.wagtail_tests import WagtailTestUtils


class TestBaseViewSet(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

    def get_main_menu_items(self, response):
        # The top-level sidebar menu items.
        soup = self.get_soup(response.content)
        sidebar_props = json.loads(soup.select_one("#wagtail-sidebar-props").text)
        main_menu_module = next(
            module
            for module in sidebar_props["modules"]
            if module["_type"] == "wagtail.sidebar.MainMenuModule"
        )
        return main_menu_module["_args"][0]

    def get_submenu_items(self, menu_items, name):
        # The child items of the named SubMenuItem within `menu_items`.
        submenu = next(
            item
            for item in menu_items
            if item["_type"] == "wagtail.sidebar.SubMenuItem"
            and item["_args"][0]["name"] == name
        )
        return submenu["_args"][1]

    def test_menu_items(self):
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertEqual(response.status_code, 200)

        main_menu = self.get_main_menu_items(response)
        misc_items = self.get_submenu_items(main_menu, "miscellaneous")

        # The Miscellaneous group's submenu contains its explicit `items` first
        # (in declaration order), followed by the items collected via its
        # `submenu_hook`: a ViewSet (via its `menu_hook`) and a plain MenuItem
        # (returned directly from the hook). Both serialize as LinkMenuItems.
        self.assertEqual(
            [
                (item["_type"], item["_args"][0]["name"], item["_args"][0]["url"])
                for item in misc_items
            ],
            [
                ("wagtail.sidebar.LinkMenuItem", "the-greetings", "/admin/greetingz/"),
                (
                    "wagtail.sidebar.LinkMenuItem",
                    "submenu-hook-planner",
                    "/admin/planner/",
                ),
                (
                    "wagtail.sidebar.LinkMenuItem",
                    "submenu-hook-greetings",
                    "/admin/submenu_hook_greetingz/",
                ),
                ("wagtail.sidebar.LinkMenuItem", "the-calendar", "/admin/calendar/"),
            ],
        )

    def test_calendar_index_view(self):
        url = reverse("calendar:index")
        response = self.client.get(url)
        now = timezone.now()
        self.assertEqual(url, "/admin/calendar/")
        self.assertContains(response, f"{now.year} calendar")

    def test_calendar_month_view(self):
        url = reverse("calendar:month")
        response = self.client.get(url)
        now = timezone.now()
        self.assertEqual(url, "/admin/calendar/month/")
        self.assertContains(response, f"{now.year}/{now.month} calendar")

    def test_greetings_view(self):
        self.user.first_name = "Gordon"
        self.user.last_name = "Freeman"
        self.user.save()
        url = reverse("greetings:index")
        response = self.client.get(url)
        self.assertEqual(url, "/admin/greetingz/")
        self.assertContains(response, "Greetings")
        self.assertContains(response, "Welcome to this greetings page, Gordon Freeman!")

    def test_submenu_hook_greetings_view(self):
        self.user.first_name = "Gordon"
        self.user.last_name = "Freeman"
        self.user.save()
        url = reverse("submenu_hook_greetings:index")
        response = self.client.get(url)
        self.assertEqual(url, "/admin/submenu_hook_greetingz/")
        self.assertContains(response, "Submenu Hook Greetings")
        self.assertContains(response, "Welcome to this greetings page, Gordon Freeman!")

    def test_method_injection(self):
        response = self.client.get(reverse("opera:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Porgy and Bess")
