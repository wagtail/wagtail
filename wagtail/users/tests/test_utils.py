from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings

from wagtail.users.utils import (
    get_gravatar_url,
    get_manageable_token_owners,
    user_can_manage_token,
)

User: Any = get_user_model()


def make_user(username_value, *, superuser=False, perms=()):
    """Create a user without assuming which field is USERNAME_FIELD."""
    kwargs = {"password": "password"}
    kwargs[User.USERNAME_FIELD] = username_value
    if User.USERNAME_FIELD != "email":
        kwargs["email"] = f"{username_value}@example.com"
    if superuser:
        return User.objects.create_superuser(**kwargs)
    user = User.objects.create_user(**kwargs)
    if perms:
        # Assigned before any has_perm call, so no permission cache to clear.
        user.user_permissions.set(Permission.objects.filter(codename__in=perms))
    return user


class TestUserCanManageToken(TestCase):
    change_user_codename = f"change_{User._meta.model_name}"

    def test_self_service_with_model_perm(self):
        user = make_user("ed", perms=["add_apitoken"])
        self.assertTrue(user_can_manage_token(user, user, "wagtailcore.add_apitoken"))

    def test_self_service_without_model_perm_denied(self):
        user = make_user("ed")
        self.assertFalse(user_can_manage_token(user, user, "wagtailcore.add_apitoken"))

    def test_cross_user_requires_change_user_perm(self):
        owner = make_user("owner")
        manager = make_user("mgr", perms=["add_apitoken", self.change_user_codename])
        self.assertTrue(
            user_can_manage_token(manager, owner, "wagtailcore.add_apitoken")
        )
        no_cross = make_user("plain", perms=["add_apitoken"])
        self.assertFalse(
            user_can_manage_token(no_cross, owner, "wagtailcore.add_apitoken")
        )

    def test_superuser_tokens_only_manageable_by_superusers(self):
        root = make_user("root", superuser=True)
        manager = make_user("mgr", perms=["add_apitoken", self.change_user_codename])
        self.assertFalse(
            user_can_manage_token(manager, root, "wagtailcore.add_apitoken")
        )
        self.assertTrue(user_can_manage_token(root, root, "wagtailcore.add_apitoken"))

    def test_manageable_owners_queryset(self):
        plain = make_user("plain", perms=["add_apitoken"])
        manager = make_user("mgr", perms=["add_apitoken", self.change_user_codename])
        root = make_user("root", superuser=True)
        self.assertQuerySetEqual(
            get_manageable_token_owners(plain), [plain], ordered=False
        )
        # Managers see everyone except superusers.
        owners = get_manageable_token_owners(manager)
        self.assertIn(plain, owners)
        self.assertNotIn(root, owners)
        # Superusers see everyone.
        self.assertIn(root, get_manageable_token_owners(root))


class TestGravatar(TestCase):
    def test_gravatar_default(self):
        """Test with the default settings"""
        self.assertEqual(
            get_gravatar_url("something@example.com"),
            "//www.gravatar.com/avatar/76ebd6fecabc982c205dd056e8f0415a?d=mp&s=100",
        )

    def test_gravatar_custom_size(self):
        """Test with a custom size (note that the size will be doubled)"""
        self.assertEqual(
            get_gravatar_url("something@example.com", size=100),
            "//www.gravatar.com/avatar/76ebd6fecabc982c205dd056e8f0415a?d=mp&s=200",
        )

    @override_settings(
        WAGTAIL_GRAVATAR_PROVIDER_URL="https://robohash.org/avatar?d=robohash&s=200"
    )
    def test_gravatar_params_that_overlap(self):
        """
        Test with params that overlap with default s (size) and d (default_image)
        Also test the `s` is not overridden by the provider URL's query parameters.
        """
        self.assertEqual(
            get_gravatar_url("something@example.com", size=80),
            "https://robohash.org/avatar/76ebd6fecabc982c205dd056e8f0415a?d=robohash&s=160",
        )

    @override_settings(WAGTAIL_GRAVATAR_PROVIDER_URL="https://robohash.org/avatar?f=y")
    def test_gravatar_params_that_dont_overlap(self):
        """Test with params that don't default `s (size)` and `d (default_image)`"""
        self.assertEqual(
            get_gravatar_url("something@example.com"),
            "https://robohash.org/avatar/76ebd6fecabc982c205dd056e8f0415a?d=mp&f=y&s=100",
        )

    @override_settings(
        WAGTAIL_GRAVATAR_PROVIDER_URL="https://robohash.org/avatar?d=robohash&f=y"
    )
    def test_gravatar_query_params_override_default_params(self):
        """Test that query parameters of `WAGTAIL_GRAVATAR_PROVIDER_URL` override default_params"""
        self.assertEqual(
            get_gravatar_url(
                "something@example.com", default_params={"d": "monsterid"}
            ),
            "https://robohash.org/avatar/76ebd6fecabc982c205dd056e8f0415a?d=robohash&f=y&s=100",
        )

    @override_settings(WAGTAIL_GRAVATAR_PROVIDER_URL="https://robohash.org/avatar/")
    def test_gravatar_trailing_slash(self):
        """Test with a trailing slash in the URL"""
        self.assertEqual(
            get_gravatar_url("something@example.com"),
            "https://robohash.org/avatar/76ebd6fecabc982c205dd056e8f0415a?d=mp&s=100",
        )

    @override_settings(WAGTAIL_GRAVATAR_PROVIDER_URL="https://robohash.org/avatar")
    def test_gravatar_no_trailing_slash(self):
        """Test with no trailing slash in the URL"""
        self.assertEqual(
            get_gravatar_url("something@example.com"),
            "https://robohash.org/avatar/76ebd6fecabc982c205dd056e8f0415a?d=mp&s=100",
        )

    @override_settings(WAGTAIL_GRAVATAR_PROVIDER_URL="https://robohash.org/avatar?")
    def test_gravatar_trailing_question_mark(self):
        """Test with a trailing question mark in the URL"""
        self.assertEqual(
            get_gravatar_url("something@example.com"),
            "https://robohash.org/avatar/76ebd6fecabc982c205dd056e8f0415a?d=mp&s=100",
        )
