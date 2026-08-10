import re
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from wagtail.log_actions import registry as log_registry
from wagtail.models import APIToken
from wagtail.users.wagtail_hooks import register_viewset

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
        # redirected with a permission error (Wagtail's default for users
        # with admin access but without the view permission)
        self.assertEqual(response.status_code, 302)

    def test_get_add_form(self):
        self.client.force_login(self.root)
        response = self.get("add")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="user"')

    def test_create_shows_secret_exactly_once(self):
        self.client.force_login(self.root)
        response = self.client.post(
            reverse("wagtailusers_apitokens:add"),
            {"user": self.root.pk, "name": "deploy bot"},
        )
        token = APIToken.objects.get()
        # POST/redirect/GET to the one-time secret page
        self.assertRedirects(
            response,
            reverse("wagtailusers_apitokens:created", args=[token.pk]),
            fetch_redirect_response=False,
        )
        created = self.client.get(response["Location"])
        self.assertEqual(created.status_code, 200)
        self.assertContains(created, token.prefix)
        matches = TOKEN_RE.findall(created.content.decode())
        self.assertEqual(len(matches), 1)
        plaintext = matches[0]

        # The one-time page does not serve the secret twice.
        second = self.client.get(response["Location"])
        self.assertEqual(second.status_code, 302)

        # The full secret is never shown anywhere else.
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
        self.assertEqual(response.status_code, 302)
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

    def test_edit_scoped_to_manageable_tokens(self):
        token, _ = APIToken.create_token(user=self.root, name="root token")
        manager = make_user(
            "mgr",
            admin_perms=["change_apitoken", f"change_{User._meta.model_name}"],
        )
        self.client.force_login(manager)
        # managers may not open the rename view for a superuser's token
        response = self.client.get(
            reverse("wagtailusers_apitokens:edit", args=[token.pk])
        )
        self.assertEqual(response.status_code, 404)
        # but can rename their own
        own, _ = APIToken.create_token(user=manager, name="mgr token")
        response = self.client.post(
            reverse("wagtailusers_apitokens:edit", args=[own.pk]),
            {"name": "renamed"},
        )
        self.assertEqual(response.status_code, 302)
        own.refresh_from_db()
        self.assertEqual(own.name, "renamed")

    def test_revoke_confirmation_scoped_to_manageable_tokens(self):
        token, _ = APIToken.create_token(user=self.root, name="root token")
        manager = make_user(
            "mgr",
            admin_perms=["delete_apitoken", f"change_{User._meta.model_name}"],
        )
        self.client.force_login(manager)
        response = self.client.get(
            reverse("wagtailusers_apitokens:delete", args=[token.pk])
        )
        self.assertEqual(response.status_code, 404)

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


class TestAPITokenViewSetRegistration(SimpleTestCase):
    def test_registered_when_v3_installed(self):
        with patch("wagtail.users.wagtail_hooks.apps.is_installed", return_value=True):
            names = [vs.name for vs in register_viewset()]
        self.assertIn("wagtailusers_apitokens", names)

    def test_omitted_when_v3_not_installed(self):
        with patch("wagtail.users.wagtail_hooks.apps.is_installed", return_value=False):
            names = [vs.name for vs in register_viewset()]
        self.assertNotIn("wagtailusers_apitokens", names)
