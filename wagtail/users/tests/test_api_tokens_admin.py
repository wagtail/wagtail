import re
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from wagtail.log_actions import registry as log_registry
from wagtail.models import APIToken
from wagtail.test.utils import WagtailTestUtils
from wagtail.users.wagtail_hooks import register_viewset

User = get_user_model()

TOKEN_RE = re.compile(r"wagtail_[0-9A-Za-z]{33}")


class TestAPITokenAdmin(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root = WagtailTestUtils.create_superuser("root")

    def get(self, url_name, params=None, **kwargs):
        url = reverse(f"wagtailusers_api_tokens:{url_name}", **kwargs)
        return self.client.get(url, params or {})

    def test_index_requires_permission(self):
        self.client.force_login(self.root)
        self.assertEqual(self.get("index").status_code, 200)

        editor = WagtailTestUtils.create_user("editor")
        self.client.force_login(editor)
        # no admin access at all: redirected to the admin login
        self.assertEqual(self.get("index").status_code, 302)

    def test_index_requires_apitoken_permission(self):
        editor = WagtailTestUtils.create_user(
            "editor", permissions=["access_admin", "access_admin"]
        )
        self.client.force_login(editor)
        response = self.get("index")
        # redirected with a permission error (Wagtail's default for users
        # with admin access but without the view permission)
        self.assertEqual(response.status_code, 302)

    def test_get_add_form(self):
        self.client.force_login(self.root)
        response = self.get("add")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="user"')

    def test_create_shows_secret_on_post_response(self):
        self.client.force_login(self.root)
        response = self.client.post(
            reverse("wagtailusers_api_tokens:add"),
            {"user": self.root.pk, "name": "deploy bot"},
        )
        token = APIToken.objects.get()
        # The token is rendered directly in the POST response (no redirect).
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, token.prefix)
        matches = TOKEN_RE.findall(response.content.decode())
        self.assertEqual(len(matches), 1)
        plaintext = matches[0]

        # The full secret is never shown anywhere else.
        self.assertNotContains(self.get("index"), plaintext)
        self.assertContains(self.get("index"), token.prefix)

    def test_create_logs_action(self):
        self.client.force_login(self.root)
        self.client.post(
            reverse("wagtailusers_api_tokens:add"),
            {"user": self.root.pk, "name": "deploy bot"},
        )
        token = APIToken.objects.get()
        actions = log_registry.get_logs_for_instance(token).values_list(
            "action", flat=True
        )
        self.assertIn("wagtail.apitoken.create", actions)

    def test_self_service_create_without_cross_user_perm(self):
        plain = WagtailTestUtils.create_user(
            "plain", permissions=["access_admin", "add_apitoken"]
        )
        self.client.force_login(plain)
        response = self.client.post(
            reverse("wagtailusers_api_tokens:add"),
            {"user": plain.pk, "name": "my token"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(APIToken.objects.get().user, plain)

    def test_create_for_other_user_requires_change_user_perm(self):
        plain = WagtailTestUtils.create_user(
            "plain", permissions=["access_admin", "add_apitoken"]
        )
        other = WagtailTestUtils.create_user("other")
        self.client.force_login(plain)
        response = self.client.post(
            reverse("wagtailusers_api_tokens:add"),
            {"user": other.pk, "name": "not allowed"},
        )
        # rejected by form validation: other users are not selectable
        self.assertEqual(response.status_code, 200)
        self.assertIn("user", response.context["form"].errors)
        self.assertFalse(APIToken.objects.exists())

    def test_manager_cannot_create_token_for_superuser(self):
        manager = WagtailTestUtils.create_user(
            "mgr",
            permissions=[
                "access_admin",
                "add_apitoken",
                f"change_{User._meta.model_name}",
            ],
        )
        self.client.force_login(manager)
        response = self.client.post(
            reverse("wagtailusers_api_tokens:add"),
            {"user": self.root.pk, "name": "escalation attempt"},
        )
        # rejected by form validation: superusers are not selectable
        self.assertEqual(response.status_code, 200)
        self.assertIn("user", response.context["form"].errors)
        self.assertFalse(APIToken.objects.exists())

    def test_index_links_to_edit_and_revoke(self):
        token, _ = APIToken.create_token(user=self.root, name="deploy bot")
        self.client.force_login(self.root)
        response = self.get("index")
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, reverse("wagtailusers_api_tokens:edit", args=[token.pk])
        )
        self.assertContains(
            response, reverse("wagtailusers_api_tokens:delete", args=[token.pk])
        )
        self.assertContains(response, "Revoke")
        self.assertNotContains(response, ">Delete<")

    def test_revoke_confirmation_uses_revoke_labels(self):
        token, _ = APIToken.create_token(user=self.root, name="deploy bot")
        self.client.force_login(self.root)
        response = self.client.get(
            reverse("wagtailusers_api_tokens:delete", args=[token.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Revoke")
        self.assertContains(response, "Are you sure you want to revoke this API token?")
        self.assertContains(response, "Yes, revoke")
        self.assertContains(response, "No, don't revoke")
        self.assertNotContains(response, "Yes, delete")
        self.assertNotContains(response, "No, don't delete")

        edit_response = self.client.get(
            reverse("wagtailusers_api_tokens:edit", args=[token.pk])
        )
        self.assertContains(edit_response, "Revoke")
        self.assertNotContains(edit_response, ">Delete<")

    def test_index_scoping(self):
        APIToken.create_token(user=self.root, name="root token")
        plain = WagtailTestUtils.create_user("plain")
        APIToken.create_token(user=plain, name="plain token")
        manager = WagtailTestUtils.create_user(
            "mgr",
            permissions=[
                "access_admin",
                "view_apitoken",
                f"change_{User._meta.model_name}",
            ],
        )
        self.client.force_login(manager)
        response = self.get("index")
        self.assertContains(response, "plain token")
        # managers may not see superusers' tokens
        self.assertNotContains(response, "root token")
        # superusers see everything
        self.client.force_login(self.root)
        response = self.get("index")
        self.assertContains(response, "root token")
        self.assertContains(response, "plain token")

    def test_index_unfiltered_self_service_scope(self):
        plain = WagtailTestUtils.create_user(
            "plain", permissions=["access_admin", "view_apitoken"]
        )
        other = WagtailTestUtils.create_user("other")
        APIToken.create_token(user=plain, name="mine")
        APIToken.create_token(user=other, name="theirs")
        self.client.force_login(plain)
        response = self.get("index")
        self.assertContains(response, "mine")
        self.assertNotContains(response, "theirs")

    def test_filter_by_user(self):
        plain = WagtailTestUtils.create_user("plain")
        other = WagtailTestUtils.create_user("other")
        APIToken.create_token(user=plain, name="plain token")
        APIToken.create_token(user=other, name="other token")
        manager = WagtailTestUtils.create_user(
            "mgr",
            permissions=[
                "access_admin",
                "view_apitoken",
                f"change_{User._meta.model_name}",
            ],
        )
        self.client.force_login(manager)
        response = self.get("index", params={"user": str(plain.pk)})
        self.assertContains(response, "plain token")
        self.assertNotContains(response, "other token")

    @freeze_time("2024-06-15 12:00:00")
    def test_filter_created_range(self):
        token, _ = APIToken.create_token(user=self.root, name="dated token")
        APIToken.objects.filter(pk=token.pk).update(
            created=timezone.now() - timezone.timedelta(days=10)
        )
        today = timezone.now().date()
        self.client.force_login(self.root)
        response = self.get(
            "index",
            params={
                "created_from": str(today - timezone.timedelta(days=30)),
                "created_to": str(today - timezone.timedelta(days=5)),
            },
        )
        self.assertContains(response, "dated token")
        response = self.get(
            "index",
            params={
                "created_from": str(today),
                "created_to": str(today),
            },
        )
        self.assertNotContains(response, "dated token")

    @freeze_time("2024-06-15 12:00:00")
    def test_filter_last_used_at_range(self):
        token, _ = APIToken.create_token(user=self.root, name="used token")
        used_at = timezone.now() - timezone.timedelta(days=3)
        APIToken.objects.filter(pk=token.pk).update(last_used_at=used_at)
        today = timezone.now().date()
        self.client.force_login(self.root)
        response = self.get(
            "index",
            params={
                "last_used_at_from": str(today - timezone.timedelta(days=7)),
                "last_used_at_to": str(today),
            },
        )
        self.assertContains(response, "used token")
        response = self.get(
            "index",
            params={
                "last_used_at_from": str(today - timezone.timedelta(days=2)),
                "last_used_at_to": str(today - timezone.timedelta(days=1)),
            },
        )
        self.assertNotContains(response, "used token")

    def test_filter_revoked(self):
        APIToken.create_token(user=self.root, name="active token")
        revoked, _ = APIToken.create_token(user=self.root, name="revoked token")
        revoked.revoke()
        self.client.force_login(self.root)
        response = self.get("index", params={"revoked": "True"})
        self.assertContains(response, "revoked token")
        self.assertNotContains(response, "active token")
        response = self.get("index", params={"revoked": "False"})
        self.assertContains(response, "active token")
        self.assertNotContains(response, "revoked token")

    def test_crafted_user_filter_cannot_bypass_scope(self):
        plain = WagtailTestUtils.create_user(
            "plain", permissions=["access_admin", "view_apitoken"]
        )
        other = WagtailTestUtils.create_user("other")
        APIToken.create_token(user=other, name="secret token")
        self.client.force_login(plain)
        response = self.get("index", params={"user": str(other.pk)})
        self.assertNotContains(response, "secret token")

    def test_edit_status_reflects_active_and_revoked(self):
        token, _ = APIToken.create_token(user=self.root, name="deploy bot")
        self.client.force_login(self.root)
        response = self.client.get(
            reverse("wagtailusers_api_tokens:edit", args=[token.pk])
        )
        self.assertContains(response, "Active")
        self.assertNotContains(response, "Status: Live")

        token.revoke()
        response = self.client.get(
            reverse("wagtailusers_api_tokens:edit", args=[token.pk])
        )
        self.assertContains(response, "Revoked")
        self.assertNotContains(response, "Active")

    def test_edit_usage_shows_last_used(self):
        token, _ = APIToken.create_token(user=self.root, name="deploy bot")
        self.client.force_login(self.root)
        response = self.client.get(
            reverse("wagtailusers_api_tokens:edit", args=[token.pk])
        )
        self.assertContains(response, "Never")
        self.assertNotContains(response, "Used 0 times")
        self.assertNotContains(
            response, reverse("wagtailusers_api_tokens:usage", args=[token.pk])
        )

        token.last_used_at = timezone.now()
        token.save(update_fields=["last_used_at"])
        response = self.client.get(
            reverse("wagtailusers_api_tokens:edit", args=[token.pk])
        )
        self.assertContains(response, "just now")
        self.assertNotContains(response, "Never")

    def test_edit_scoped_to_manageable_tokens(self):
        token, _ = APIToken.create_token(user=self.root, name="root token")
        manager = WagtailTestUtils.create_user(
            "mgr",
            permissions=[
                "access_admin",
                "change_apitoken",
                f"change_{User._meta.model_name}",
            ],
        )
        self.client.force_login(manager)
        # managers may not open the rename view for a superuser's token
        response = self.client.get(
            reverse("wagtailusers_api_tokens:edit", args=[token.pk])
        )
        self.assertEqual(response.status_code, 404)
        # but can rename their own
        own, _ = APIToken.create_token(user=manager, name="mgr token")
        response = self.client.post(
            reverse("wagtailusers_api_tokens:edit", args=[own.pk]),
            {"name": "renamed"},
        )
        self.assertEqual(response.status_code, 302)
        own.refresh_from_db()
        self.assertEqual(own.name, "renamed")

    def test_revoke_confirmation_scoped_to_manageable_tokens(self):
        token, _ = APIToken.create_token(user=self.root, name="root token")
        manager = WagtailTestUtils.create_user(
            "mgr",
            permissions=[
                "access_admin",
                "delete_apitoken",
                f"change_{User._meta.model_name}",
            ],
        )
        self.client.force_login(manager)
        response = self.client.get(
            reverse("wagtailusers_api_tokens:delete", args=[token.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_revoke_soft_deletes_and_logs(self):
        token, _ = APIToken.create_token(user=self.root, name="deploy bot")
        self.client.force_login(self.root)
        response = self.client.post(
            reverse("wagtailusers_api_tokens:delete", args=[token.pk])
        )
        self.assertEqual(response.status_code, 302)
        token.refresh_from_db()
        self.assertIsNotNone(token.revoked_at)
        # the row is kept for the audit trail
        self.assertTrue(APIToken.objects.filter(pk=token.pk).exists())
        actions = log_registry.get_logs_for_instance(token).values_list(
            "action", flat=True
        )
        self.assertIn("wagtail.apitoken.revoke", actions)


class TestAPITokenViewSetRegistration(SimpleTestCase):
    def test_registered_when_v3_installed(self):
        with patch("wagtail.users.wagtail_hooks.apps.is_installed", return_value=True):
            names = [vs.name for vs in register_viewset()]
        self.assertIn("wagtailusers_api_tokens", names)

    def test_omitted_when_v3_not_installed(self):
        with patch("wagtail.users.wagtail_hooks.apps.is_installed", return_value=False):
            names = [vs.name for vs in register_viewset()]
        self.assertNotIn("wagtailusers_api_tokens", names)
