from django.test import TestCase, override_settings

from wagtail.documents import get_document_model
from wagtail.permission_policies.collections import CollectionOwnershipPermissionPolicy
from wagtail.permissions import policies_registry
from wagtail.test.testapp.models import CustomDocument
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

    @override_settings(WAGTAILDOCS_DOCUMENT_MODEL="tests.CustomDocument")
    def test_get_from_registry_with_custom_model(self):
        permission_policy = policies_registry.get_by_type(CustomDocument)
        self.assertIsInstance(permission_policy, CollectionOwnershipPermissionPolicy)
        self.assertIs(permission_policy.model, CustomDocument)
