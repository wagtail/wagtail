from wagtail.documents import get_document_model_string
from wagtail.permissions import override_permission_policy
from wagtail.permission_policies.collections import CollectionOwnershipPermissionPolicy

permission_policy = override_permission_policy("document",CollectionOwnershipPermissionPolicy(
    get_document_model_string(),
    auth_model="wagtaildocs.Document",
    owner_field_name="uploaded_by_user",
    ),
)
