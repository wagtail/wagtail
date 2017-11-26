from wagtail.core.permission_policies.collections import CollectionOwnershipPermissionPolicy
from wagtail.images import get_image_model
from wagtail.images.models import Image

permission_policy = CollectionOwnershipPermissionPolicy(
    get_image_model(),
    auth_model=Image,
    owner_field_name='uploaded_by_user'
)
