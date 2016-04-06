from wagtail.wagtailcore.permission_policies.collections import (
    CollectionOwnershipPermissionPolicy
)
from wagtail.wagtailimages.models import Image, get_image_model


permission_policy = CollectionOwnershipPermissionPolicy(
    get_image_model(),
    auth_model=Image,
    owner_field_name='uploaded_by_user'
)
