from django.test import TestCase

from wagtail.documents import get_document_model
from wagtail.permission_policies.collections import CollectionOwnershipPermissionPolicy
from wagtail.permissions import policies_registry
from wagtail.utils.deprecation import RemovedInWagtail90Warning


class TestDocumentPermissions(TestCase):
    def test_permissions_direct_import_deprecated(self):
        model = get_document_model()
        with self.assertWarnsMessage(
            RemovedInWagtail90Warning,
            "wagtail.documents.permissions.permission_policy is deprecated. "
            "Use wagtail.permissions.policies_registry.get_by_type(get_document_model()) instead.",
        ):
            from wagtail.documents.permissions import permission_policy

            self.assertIsInstance(
                permission_policy,
                CollectionOwnershipPermissionPolicy,
            )
            self.assertIs(permission_policy.model, model)

    def test_get_from_registry(self):
        model = get_document_model()
        permission_policy = policies_registry.get_by_type(model)
        self.assertIsInstance(permission_policy, CollectionOwnershipPermissionPolicy)
        self.assertIs(permission_policy.model, model)
