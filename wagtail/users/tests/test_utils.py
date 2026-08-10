from typing import Any

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from wagtail.test.utils import WagtailTestUtils
from wagtail.users.utils import (
    get_gravatar_url,
    get_manageable_token_owners,
    user_can_manage_token,
)

User: Any = get_user_model()


class TestUserCanManageToken(TestCase):
    change_user_codename = f"change_{User._meta.model_name}"

    def test_self_service_with_model_perm(self):
        user = WagtailTestUtils.create_user("ed", permissions=["add_apitoken"])
        self.assertTrue(user_can_manage_token(user, user, "wagtailcore.add_apitoken"))

    def test_self_service_without_model_perm_denied(self):
        user = WagtailTestUtils.create_user("ed")
        self.assertFalse(user_can_manage_token(user, user, "wagtailcore.add_apitoken"))

    def test_cross_user_requires_change_user_perm(self):
        owner = WagtailTestUtils.create_user("owner")
        manager = WagtailTestUtils.create_user(
            "mgr", permissions=["add_apitoken", self.change_user_codename]
        )
        self.assertTrue(
            user_can_manage_token(manager, owner, "wagtailcore.add_apitoken")
        )
        no_cross = WagtailTestUtils.create_user("plain", permissions=["add_apitoken"])
        self.assertFalse(
            user_can_manage_token(no_cross, owner, "wagtailcore.add_apitoken")
        )

    def test_superuser_tokens_only_manageable_by_superusers(self):
        root = WagtailTestUtils.create_superuser("root")
        manager = WagtailTestUtils.create_user(
            "mgr", permissions=["add_apitoken", self.change_user_codename]
        )
        self.assertFalse(
            user_can_manage_token(manager, root, "wagtailcore.add_apitoken")
        )
        self.assertTrue(user_can_manage_token(root, root, "wagtailcore.add_apitoken"))

    def test_manageable_owners_queryset(self):
        plain = WagtailTestUtils.create_user("plain", permissions=["add_apitoken"])
        manager = WagtailTestUtils.create_user(
            "mgr", permissions=["add_apitoken", self.change_user_codename]
        )
        root = WagtailTestUtils.create_superuser("root")
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
