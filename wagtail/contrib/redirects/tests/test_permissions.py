from django.test import TestCase

from wagtail.contrib.redirects.models import Redirect
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.permissions import policy_registry
from wagtail.utils.deprecation import RemovedInWagtail90Warning


class TestRedirectPermissions(TestCase):
    def test_permissions_direct_import_deprecated(self):
        with self.assertWarnsMessage(
            RemovedInWagtail90Warning,
            "wagtail.contrib.redirects.permissions.permission_policy is deprecated. "
            "Use wagtail.permissions.policy_registry.get_by_type(Redirect) instead.",
        ):
            from wagtail.contrib.redirects.permissions import permission_policy

            self.assertIsInstance(permission_policy, ModelPermissionPolicy)
            self.assertIs(permission_policy.model, Redirect)

    def test_get_from_registry(self):
        permission_policy = policy_registry.get_by_type(Redirect)
        self.assertIsInstance(permission_policy, ModelPermissionPolicy)
        self.assertIs(permission_policy.model, Redirect)
