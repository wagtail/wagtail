from wagtail.models.sites import Site
from wagtail.permission_policies.base import BasePermissionPolicy, ModelPermissionPolicy
from django.test import TestCase, override_settings
from wagtail.permissions import get_permission_policy


class TestPermissionPolicy(BasePermissionPolicy):
    pass


class TestOverridePermissionPolicy(TestCase):
    # Test that the default permission policy is returned when no override is set
    def test_get_permission_policy_without_override(self):
        policy = get_permission_policy("test", ModelPermissionPolicy)(Site)

        self.assertIsInstance(policy, ModelPermissionPolicy)
        self.assertNotIsInstance(policy, TestPermissionPolicy)

    # Test overriding the permission policy using the WAGTAIL_PERMISSION_POLICY_OVERRIDES setting
    @override_settings(WAGTAIL_PERMISSION_POLICY_OVERRIDES={"test": "wagtail.tests.permission_policies.TestPermissionPolicy"})
    def test_get_permission_policy_with_override(self):
        policy = get_permission_policy("test", ModelPermissionPolicy)(Site)

        self.assertNotIsInstance(policy, ModelPermissionPolicy)
        self.assertIsInstance(policy, TestPermissionPolicy)
        self.assertIsInstance(policy, BasePermissionPolicy)