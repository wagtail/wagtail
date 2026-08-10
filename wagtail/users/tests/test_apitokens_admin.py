import re

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.log_actions import registry as log_registry
from wagtail.models import APIToken

User = get_user_model()

TOKEN_RE = re.compile(r"wagtail_[0-9A-Za-z]{33}")


def make_user(username_value, *, superuser=False, admin_perms=()):
    """Create a user, optionally with admin access and extra permissions."""
    kwargs = {"password": "password"}
    kwargs[User.USERNAME_FIELD] = username_value
    if User.USERNAME_FIELD != "email":
        kwargs["email"] = f"{username_value}@example.com"
    if superuser:
        return User.objects.create_superuser(**kwargs)
    user = User.objects.create_user(**kwargs)
    if admin_perms:
        group = Group.objects.create(name=f"group-{username_value}")
        group.permissions.set(
            Permission.objects.filter(codename__in=["access_admin", *admin_perms])
        )
        user.groups.add(group)
    return user


class TestAPITokenAdmin(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root = make_user("root", superuser=True)

    def get(self, url_name, **kwargs):
        return self.client.get(reverse(f"wagtailusers_apitokens:{url_name}", **kwargs))

    def test_index_requires_permission(self):
        self.client.force_login(self.root)
        self.assertEqual(self.get("index").status_code, 200)

        editor = make_user("editor", admin_perms=[])
        self.client.force_login(editor)
        # no admin access at all: redirected to the admin login
        self.assertEqual(self.get("index").status_code, 302)

    def test_index_requires_apitoken_permission(self):
        editor = make_user("editor", admin_perms=["access_admin"])
        self.client.force_login(editor)
        response = self.get("index")
        self.assertIn(response.status_code, (302, 403))

    def test_get_add_form(self):
        self.client.force_login(self.root)
        response = self.get("add")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "name")

    def test_create_shows_secret_exactly_once(self):
        self.client.force_login(self.root)
        response = self.client.post(
            reverse("wagtailusers_apitokens:add"),
            {"user": self.root.pk, "name": "deploy bot"},
        )
        self.assertEqual(response.status_code, 200)
        token = APIToken.objects.get()
        self.assertContains(response, token.prefix)
        match = TOKEN_RE.search(response.content.decode())
        self.assertIsNotNone(match)
        plaintext = match.group()

        # The full secret is never shown again.
        self.assertNotContains(self.get("index"), plaintext)
        self.assertContains(self.get("index"), token.prefix)

    def test_create_logs_action(self):
        self.client.force_login(self.root)
        self.client.post(
            reverse("wagtailusers_apitokens:add"),
            {"user": self.root.pk, "name": "deploy bot"},
        )
        token = APIToken.objects.get()
        actions = log_registry.get_logs_for_instance(token).values_list(
            "action", flat=True
        )
        self.assertIn("wagtail.apitoken.create", actions)

    def test_self_service_create_without_cross_user_perm(self):
        plain = make_user("plain", admin_perms=["add_apitoken"])
        self.client.force_login(plain)
        response = self.client.post(
            reverse("wagtailusers_apitokens:add"),
            {"user": plain.pk, "name": "my token"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(APIToken.objects.get().user, plain)

    def test_create_for_other_user_requires_change_user_perm(self):
        plain = make_user("plain", admin_perms=["add_apitoken"])
        other = make_user("other")
        self.client.force_login(plain)
        response = self.client.post(
            reverse("wagtailusers_apitokens:add"),
            {"user": other.pk, "name": "not allowed"},
        )
        # rejected by form validation: other users are not selectable
        self.assertEqual(response.status_code, 200)
        self.assertIn("user", response.context["form"].errors)
        self.assertFalse(APIToken.objects.exists())

    def test_manager_cannot_create_token_for_superuser(self):
        manager = make_user(
            "mgr",
            admin_perms=["add_apitoken", f"change_{User._meta.model_name}"],
        )
        self.client.force_login(manager)
        response = self.client.post(
            reverse("wagtailusers_apitokens:add"),
            {"user": self.root.pk, "name": "escalation attempt"},
        )
        # rejected by form validation: superusers are not selectable
        self.assertEqual(response.status_code, 200)
        self.assertIn("user", response.context["form"].errors)
        self.assertFalse(APIToken.objects.exists())

    def test_index_scoping(self):
        APIToken.create_token(user=self.root, name="root token")
        plain = make_user("plain")
        APIToken.create_token(user=plain, name="plain token")
        manager = make_user(
            "mgr",
            admin_perms=["view_apitoken", f"change_{User._meta.model_name}"],
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

    def test_revoke_soft_deletes_and_logs(self):
        token, _ = APIToken.create_token(user=self.root, name="deploy bot")
        self.client.force_login(self.root)
        response = self.client.post(
            reverse("wagtailusers_apitokens:delete", args=[token.pk])
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
