from django.test import TestCase, override_settings

from wagtail.images import get_image_model
from wagtail.permission_policies.collections import CollectionOwnershipPermissionPolicy
from wagtail.permissions import policies_registry
from wagtail.test.testapp.models import CustomImage
from wagtail.utils.deprecation import RemovedInWagtail90Warning


class TestImagePermissions(TestCase):
    def test_permissions_direct_import_deprecated(self):
        model = get_image_model()
        with self.assertWarnsMessage(
            RemovedInWagtail90Warning,
            "wagtail.images.permissions.permission_policy is deprecated. "
            "Use wagtail.permissions.policies_registry.get_by_type(get_image_model()) instead.",
        ):
            from wagtail.images.permissions import permission_policy

            self.assertIsInstance(
                permission_policy,
                CollectionOwnershipPermissionPolicy,
            )
            self.assertIs(permission_policy.model, model)

    def test_get_from_registry(self):
        model = get_image_model()
        permission_policy = policies_registry.get_by_type(model)
        self.assertIsInstance(permission_policy, CollectionOwnershipPermissionPolicy)
        self.assertIs(permission_policy.model, model)

    @override_settings(WAGTAILIMAGES_IMAGE_MODEL="tests.CustomImage")
    def test_get_from_registry_with_custom_model(self):
        permission_policy = policies_registry.get_by_type(CustomImage)
        self.assertIsInstance(permission_policy, CollectionOwnershipPermissionPolicy)
        self.assertIs(permission_policy.model, CustomImage)
