from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.test.testapp.models import Advert
from wagtail.test.utils import WagtailTestUtils


class TestAddOnlyPermissions(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.test_snippet = Advert.objects.get(pk=1)

        # Create a user with add_advert permission but not change_advert
        user = self.create_user(
            username="addonly", email="addonly@example.com", password="password"
        )
        add_permission = Permission.objects.get(
            content_type__app_label="tests", codename="add_advert"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        user.user_permissions.add(add_permission, admin_permission)
        self.login(username="addonly", password="password")

    def test_get_index(self):
        response = self.client.get(reverse("wagtailsnippets_tests_advert:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/index.html")

        # user should get an "Add advert" button
        self.assertContains(response, "Add advert")

    def test_get_add(self):
        response = self.client.get(reverse("wagtailsnippets_tests_advert:add"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/create.html")
        self.assertEqual(response.context["header_icon"], "snippet")

    def test_get_edit(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:edit",
                args=[quote(self.test_snippet.pk)],
            )
        )
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_delete(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:delete",
                args=[quote(self.test_snippet.pk)],
            )
        )
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))


class TestEditOnlyPermissions(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.test_snippet = Advert.objects.get(pk=1)

        # Create a user with change_advert permission but not add_advert
        user = self.create_user(
            username="changeonly", email="changeonly@example.com", password="password"
        )
        change_permission = Permission.objects.get(
            content_type__app_label="tests", codename="change_advert"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        user.user_permissions.add(change_permission, admin_permission)
        self.login(username="changeonly", password="password")

    def test_get_index(self):
        response = self.client.get(reverse("wagtailsnippets_tests_advert:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/index.html")

        # user should not get an "Add advert" button
        self.assertNotContains(response, "Add advert")

    def test_get_add(self):
        response = self.client.get(reverse("wagtailsnippets_tests_advert:add"))
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_edit(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:edit",
                args=[quote(self.test_snippet.pk)],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/edit.html")
        self.assertEqual(response.context["header_icon"], "snippet")

    def test_get_delete(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:delete",
                args=[quote(self.test_snippet.pk)],
            )
        )
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))


class TestDeleteOnlyPermissions(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.test_snippet = Advert.objects.get(pk=1)

        # Create a user with delete_advert permission
        user = self.create_user(username="deleteonly", password="password")
        change_permission = Permission.objects.get(
            content_type__app_label="tests", codename="delete_advert"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        user.user_permissions.add(change_permission, admin_permission)
        self.login(username="deleteonly", password="password")

    def test_get_index(self):
        response = self.client.get(reverse("wagtailsnippets_tests_advert:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/index.html")

        # user should not get an "Add advert" button
        self.assertNotContains(response, "Add advert")

    def test_get_add(self):
        response = self.client.get(reverse("wagtailsnippets_tests_advert:add"))
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_edit(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:edit",
                args=[quote(self.test_snippet.pk)],
            )
        )
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_delete(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:delete",
                args=[quote(self.test_snippet.pk)],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/confirm_delete.html")
        self.assertEqual(response.context["header_icon"], "snippet")
