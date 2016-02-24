from wagtail.wagtailcore.permission_policies import OwnershipPermissionPolicy
from wagtail.wagtaildocs.models import Document, get_document_model


permission_policy = OwnershipPermissionPolicy(
    get_document_model(),
    auth_model=Document,
    owner_field_name='uploaded_by_user'
)
