from django.contrib.admin.utils import quote
from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.test.testapp.models import FullFeaturedSnippet
from wagtail.test.utils import WagtailTestUtils


class TestIndexViewReordering(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        # This model extends Orderable, thus it has a sort_order_field on the model
        # and we don't need to set it on the viewset.
        self.obj1 = FullFeaturedSnippet.objects.create(text="Toy 1", sort_order=0)
        self.obj2 = FullFeaturedSnippet.objects.create(text="Toy 2", sort_order=1)
        self.obj3 = FullFeaturedSnippet.objects.create(text="Toy 3", sort_order=2)

    def get_url_name(self, name):
        return FullFeaturedSnippet.snippet_viewset.get_url_name(name)

    def test_header_button_rendered(self):
        index_url = reverse(self.get_url_name("list"))
        custom_ordering_url = index_url + "?ordering=sort_order"
        response = self.client.get(index_url)
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        button = soup.select_one(
            f".w-slim-header .w-dropdown a[href='{custom_ordering_url}']"
        )
        self.assertIsNotNone(button)
        self.assertEqual(button.text.strip(), "Sort item order")

        # Reordering feature disabled when not sorting by sort_order,
        # the bulk actions column is present instead
        table = soup.select_one("main table")
        self.assertIsNotNone(table)
        self.assertFalse(table.get("data-controller"))
        bulk_actions_all = soup.select_one(
            "main thead th:first-child input[type='checkbox']"
        )
        self.assertIsNotNone(bulk_actions_all)
        self.assertTrue(
            bulk_actions_all.has_attr("data-bulk-action-select-all-checkbox")
        )

    def test_show_ordering_column(self):
        index_url = reverse(self.get_url_name("list"))
        custom_ordering_url = index_url + "?ordering=sort_order"
        response = self.client.get(custom_ordering_url)
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        # The table should have the w-orderable controller
        table = soup.select_one("main table")
        self.assertIsNotNone(table)
        self.assertEqual(table.get("data-controller"), "w-orderable")
        self.assertEqual(
            table.get("data-w-orderable-message-value"),
            "'__LABEL__' has been moved successfully.",
        )
        self.assertEqual(
            table.get("data-w-orderable-url-value"),
            reverse(self.get_url_name("reorder"), args=[999999]),
        )

        # The bulk actions column should not be present
        bulk_actions_all = table.select_one(
            "thead th:first-child input[type='checkbox']"
        )
        self.assertIsNone(bulk_actions_all)

        # The ordering column added as the first column
        first_th = table.select_one("thead th:first-child")
        self.assertIsNotNone(first_th)
        self.assertEqual(first_th.text.strip(), "Sort")

        # All rows have the corresponding attributes for reordering
        rows = table.select("tbody tr")
        self.assertEqual(len(rows), 3)
        expected = [
            {
                "id": f"item_{quote(obj.pk)}",
                "data-w-orderable-item-id": str(quote(obj.pk)),
                "data-w-orderable-item-label": str(obj),
                "data-w-orderable-target": "item",
            }
            for obj in [self.obj1, self.obj2, self.obj3]
        ]
        for row, expected_attrs in zip(rows, expected):
            for attr, value in expected_attrs.items():
                self.assertEqual(row.get(attr), value)
            handle = row.select_one("td button[data-w-orderable-target='handle']")
            self.assertIsNotNone(handle)

    def test_reordering_disabled_with_insufficient_permission(self):
        self.user.is_superuser = False
        self.user.save()
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        view_permission = Permission.objects.get(
            content_type__app_label=self.obj1._meta.app_label,
            codename=get_permission_codename("view", self.obj1._meta),
        )
        self.user.user_permissions.add(admin_permission, view_permission)

        index_url = reverse(self.get_url_name("list"))
        custom_ordering_url = index_url + "?ordering=sort_order"
        response = self.client.get(custom_ordering_url)
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        # Header button for enabling reordering should not be rendered
        button = soup.select_one(
            f".w-slim-header .w-dropdown a[href='{custom_ordering_url}']"
        )
        self.assertIsNone(button)

        # Reordering feature not enabled
        table = soup.select_one("main table")
        self.assertIsNotNone(table)
        self.assertFalse(table.get("data-controller"))
        bulk_actions_all = soup.select_one(
            "main thead th:first-child input[type='checkbox']"
        )
        self.assertIsNotNone(bulk_actions_all)
        self.assertTrue(
            bulk_actions_all.has_attr("data-bulk-action-select-all-checkbox")
        )

    def test_minimal_permission(self):
        self.user.is_superuser = False
        self.user.save()
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        change_permission = Permission.objects.get(
            content_type__app_label=self.obj1._meta.app_label,
            codename=get_permission_codename("change", self.obj1._meta),
        )
        self.user.user_permissions.add(admin_permission, change_permission)

        self.test_header_button_rendered()
        self.test_show_ordering_column()


class TestReorderView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.obj1 = FullFeaturedSnippet.objects.create(text="Toy 1", sort_order=0)
        self.obj2 = FullFeaturedSnippet.objects.create(text="Toy 2", sort_order=1)
        self.obj3 = FullFeaturedSnippet.objects.create(text="Toy 3", sort_order=2)

    def get_url(self, toy):
        return reverse(
            FullFeaturedSnippet.snippet_viewset.get_url_name("reorder"),
            args=(quote(toy.pk),),
        )

    def assertOrder(self, toys):
        self.assertSequenceEqual(
            list(FullFeaturedSnippet.objects.order_by("sort_order")), toys
        )

    def test_get_request_does_not_alter_order(self):
        response = self.client.get(self.get_url(self.obj1))
        self.assertEqual(response.status_code, 405)

        # Ensure item order does not change
        self.assertOrder([self.obj1, self.obj2, self.obj3])

    def test_post_request_without_position_argument_moves_to_the_end(self):
        response = self.client.post(self.get_url(self.obj1))
        self.assertEqual(response.status_code, 200)

        # Item should be moved to the end
        self.assertOrder([self.obj2, self.obj3, self.obj1])

    def test_post_request_with_non_integer_position_moves_to_the_end(self):
        response = self.client.post(self.get_url(self.obj1) + "?position=good")
        self.assertEqual(response.status_code, 200)

        # Item should be moved to the end
        self.assertOrder([self.obj2, self.obj3, self.obj1])

    def test_move_position_up(self):
        # Move toy3 to the first position
        response = self.client.post(self.get_url(self.obj3) + "?position=0")
        self.assertEqual(response.status_code, 200)

        # Check if toy3 is now the first item
        self.assertOrder([self.obj3, self.obj1, self.obj2])

    def test_move_position_down(self):
        # Move toy1 to the second position
        response = self.client.post(self.get_url(self.obj1) + "?position=1")
        self.assertEqual(response.status_code, 200)

        # Check if toy1 is now the second item
        self.assertOrder([self.obj2, self.obj1, self.obj3])

    def test_move_position_to_same_position(self):
        # Move toy1 to position 0 (where it already is)
        response = self.client.post(self.get_url(self.obj1) + "?position=0")
        self.assertEqual(response.status_code, 200)

        # Ensure item order does not change
        self.assertOrder([self.obj1, self.obj2, self.obj3])

    def test_move_position_with_invalid_target_position(self):
        response = self.client.post(self.get_url(self.obj1) + "?position=99")
        self.assertEqual(response.status_code, 200)

        # The item will be moved to the last position
        self.assertOrder([self.obj2, self.obj3, self.obj1])

    def test_insufficient_permission(self):
        self.user.is_superuser = False
        self.user.save()
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        view_permission = Permission.objects.get(
            content_type__app_label=self.obj1._meta.app_label,
            codename=get_permission_codename("view", self.obj1._meta),
        )
        self.user.user_permissions.add(admin_permission, view_permission)

        response = self.client.post(self.get_url(self.obj1) + "?position=1")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("wagtailadmin_home"))
        self.assertOrder([self.obj1, self.obj2, self.obj3])

    def test_minimal_permission(self):
        self.user.is_superuser = False
        self.user.save()
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        change_permission = Permission.objects.get(
            content_type__app_label=self.obj1._meta.app_label,
            codename=get_permission_codename("change", self.obj1._meta),
        )
        self.user.user_permissions.add(admin_permission, change_permission)

        response = self.client.post(self.get_url(self.obj1) + "?position=1")
        self.assertEqual(response.status_code, 200)

        # Check if toy1 is now the second item
        self.assertOrder([self.obj2, self.obj1, self.obj3])
