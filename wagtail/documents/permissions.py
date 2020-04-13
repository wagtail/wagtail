from wagtail.core.permission_policies.collections import CollectionOwnershipPermissionPolicy
from wagtail.documents import get_document_model

permission_policy = CollectionOwnershipPermissionPolicy(
    get_document_model(),
    auth_model=get_document_model(),
    owner_field_name='uploaded_by_user'
)
