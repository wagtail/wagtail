from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.permissions import policies_registry


class TestPermissions(TestCase):
    def test_get_user_permission_policy_from_registry(self):
        User = get_user_model()
        permission_policy = policies_registry.get_by_type(User)
        self.assertIsInstance(permission_policy, ModelPermissionPolicy)
        self.assertIs(permission_policy.model, User)

    def test_get_group_permission_policy_from_registry(self):
        permission_policy = policies_registry.get_by_type(Group)
        self.assertIsInstance(permission_policy, ModelPermissionPolicy)
        self.assertIs(permission_policy.model, Group)
