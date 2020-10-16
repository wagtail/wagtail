from wagtail.core.permission_policies.collections import CollectionOwnershipPermissionPolicy
from wagtail.documents import get_document_model
from wagtail.documents.models import Document


permission_policy = CollectionOwnershipPermissionPolicy(
    get_document_model(),
    auth_model=Document,
    owner_field_name='uploaded_by_user'
)
