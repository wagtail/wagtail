import unittest

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode

from wagtail.test.testapp.models import VariousOnDeleteModel
from wagtail.test.utils import WagtailTestUtils
from wagtail.users.views.bulk_actions.user_bulk_action import UserBulkAction

User = get_user_model()


class TestUserDeleteView(WagtailTestUtils, TestCase):
    @classmethod
    def setUpTestData(cls):
        # create a set of test users
        cls.test_users = [
            cls.create_user(
                username=f"testuser-{i}",
                email=f"testuser{i}@email.com",
                password=f"password-{i}",
            )
            for i in range(1, 6)
        ]
        # also create a superuser to delete
        cls.superuser = cls.create_superuser(
            username="testsuperuser",
            email="testsuperuser@email.com",
            password="password",
        )
        cls.base_url = (
            reverse(
                "wagtail_bulk_action",
                args=(
                    User._meta.app_label,
                    User._meta.model_name,
                    "delete",
                ),
            )
            + "?"
        )
        cls.query_params = {
            "next": reverse("wagtailusers_users:index"),
            "id": [user.pk for user in cls.test_users],
        }
        cls.url = cls.base_url + urlencode(cls.query_params, doseq=True)

        cls.superuser_delete_url = cls.base_url + f"id={cls.superuser.pk}"

    def setUp(self):
        self.current_user = self.login()
        self.self_delete_url = self.base_url + f"id={self.current_user.pk}"

    def test_simple(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailusers/bulk_actions/confirm_bulk_delete.html"
        )

    def test_user_permissions_required(self):
        # Log in with a user that doesn't have permission to delete users
        user = self.create_user(username="editor", password="password")
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        user.user_permissions.add(admin_permission)
        self.login(username="editor", password="password")

        response = self.client.get(self.url)
        self.assertRedirects(response, "/admin/")

    def test_bulk_delete(self):
        response = self.client.post(self.url)

        # Should redirect back to index
        self.assertEqual(response.status_code, 302)

        # Check that the users were deleted
        for user in self.test_users:
            self.assertFalse(User.objects.filter(email=user.email).exists())

    def test_user_cannot_delete_self(self):
        response = self.client.get(self.self_delete_url)

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertInHTML("<p>You don't have permission to delete this user</p>", html)

        needle = "<ul>"
        needle += f"<li>{self.current_user.email}</li>"
        needle += "</ul>"
        self.assertInHTML(needle, html)

        self.client.post(self.self_delete_url)

        # Check user was not deleted
        self.assertTrue(User.objects.filter(pk=self.current_user.pk).exists())

    def test_user_can_delete_other_superuser(self):
        response = self.client.get(self.superuser_delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailusers/bulk_actions/confirm_bulk_delete.html"
        )

        response = self.client.post(self.superuser_delete_url)
        # Should redirect back to index
        self.assertEqual(response.status_code, 302)

        # Check that the user was deleted
        users = User.objects.filter(email=self.superuser.email)
        self.assertEqual(users.count(), 0)

    def test_before_delete_user_hook_post(self):
        def hook_func(request, action_type, users, action_class_instance):
            self.assertEqual(action_type, "delete")
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(action_class_instance, UserBulkAction)
            self.assertCountEqual(
                [user.pk for user in self.test_users], [user.pk for user in users]
            )

            return HttpResponse("Overridden!")

        with self.register_hook("before_bulk_action", hook_func):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        for user in self.test_users:
            self.assertTrue(User.objects.filter(email=user.email).exists())

    def test_after_delete_user_hook(self):
        def hook_func(request, action_type, users, action_class_instance):
            self.assertEqual(action_type, "delete")
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(action_class_instance, UserBulkAction)

            return HttpResponse("Overridden!")

        with self.register_hook("after_bulk_action", hook_func):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        for user in self.test_users:
            self.assertFalse(User.objects.filter(email=user.email).exists())

    def test_delete_get_with_protected_reference(self):
        protected = self.test_users[0]
        model_name = User._meta.verbose_name
        with self.captureOnCommitCallbacks(execute=True):
            VariousOnDeleteModel.objects.create(
                text="Undeletable",
                protected_user=protected,
            )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        main = soup.select_one("main")
        usage_link = main.find(
            "a",
            href=reverse("wagtailusers_users:usage", args=[protected.pk])
            + "?describe_on_delete=1",
        )
        self.assertIsNotNone(usage_link)
        self.assertEqual(
            usage_link.text.strip(), f"This {model_name} is referenced 1 time."
        )
        self.assertContains(
            response,
            f"One or more references to this {model_name} prevent it from being deleted.",
        )
        submit_button = main.select_one("form button[type=submit]")
        self.assertIsNone(submit_button)
        back_button = main.find("a", href=reverse("wagtailusers_users:index"))
        self.assertIsNotNone(back_button)
        self.assertEqual(back_button.text.strip(), "Go back")

    def test_delete_post_with_protected_reference(self):
        protected = self.test_users[0]
        with self.captureOnCommitCallbacks(execute=True):
            VariousOnDeleteModel.objects.create(
                text="Undeletable",
                protected_user=protected,
            )
        response = self.client.post(self.url)

        # Should throw a PermissionDenied error and redirect to the dashboard
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("wagtailadmin_home"))
        self.assertEqual(
            response.context["message"],
            "Sorry, you do not have permission to access this area.",
        )

        # Check that the user is still here
        self.assertTrue(User.objects.filter(pk=protected.pk).exists())

    def test_with_search(self):
        self.create_user(
            username="raz",
            email="raz@email.com",
            password="password",
            first_name="Razputin",
            last_name="Aquato",
        )
        response = self.client.get(
            reverse(
                "wagtail_bulk_action",
                args=(User._meta.app_label, User._meta.model_name, "delete"),
            ),
            {"q": "raz", "id": "all"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Razputin")
        self.assertNotContains(response, "testuser")

    @unittest.skipUnless(
        settings.AUTH_USER_MODEL == "customuser.CustomUser",
        "Only applicable to CustomUser",
    )
    def test_with_search_backend(self):
        self.create_user(
            username="raz",
            email="raz@email.com",
            password="password",
            first_name="Razputin",
            last_name="Aquato",
            country="Grulovia",
        )
        response = self.client.get(
            reverse(
                "wagtail_bulk_action",
                args=(User._meta.app_label, User._meta.model_name, "delete"),
            ),
            # The country field is defined in the model's search_fields,
            # which only works with an indexed model
            {"q": "gru", "id": "all"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Razputin")
        self.assertNotContains(response, "testuser")
