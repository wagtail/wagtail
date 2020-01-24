from wagtail.core.permission_policies.collections import CollectionOwnershipPermissionPolicy
from wagtail.images import get_image_model

permission_policy = CollectionOwnershipPermissionPolicy(
    get_image_model(),
    auth_model=get_image_model(),
    owner_field_name='uploaded_by_user'
)
