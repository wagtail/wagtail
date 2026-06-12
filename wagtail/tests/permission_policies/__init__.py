from wagtail.models.sites import Site
from wagtail.permission_policies.base import ModelPermissionPolicy
from django.test import TestCase, override_settings
from wagtail.permission_policies import override_permission_policy


class TestPermissionPolicy(ModelPermissionPolicy):
    pass


class TestOverridePermissionPolicy(TestCase):
    # Test that the default permission policy is returned when no override is set
    def test_override_permission_policy_without_override(self):
        default = ModelPermissionPolicy(Site)
        policy = override_permission_policy("test", default)

        self.assertEqual(policy, default)
        self.assertNotIsInstance(policy, TestPermissionPolicy)

    # Test overriding the permission policy using the WAGTAIL_PERMISSION_POLICY_OVERRIDES setting
    @override_settings(WAGTAIL_PERMISSION_POLICY_OVERRIDES={"test": TestPermissionPolicy(Site)})
    def test_override_permission_policy_with_override(self):
        default = ModelPermissionPolicy(Site)
        policy = override_permission_policy("test", default)

        self.assertNotEqual(policy, default)
        self.assertIsInstance(policy, TestPermissionPolicy)