from __future__ import absolute_import, unicode_literals

from wagtail.wagtailcore.permission_policies.collections import CollectionOwnershipPermissionPolicy
from wagtail.wagtailimages import get_image_model
from wagtail.wagtailimages.models import Image

permission_policy = CollectionOwnershipPermissionPolicy(
    get_image_model(),
    auth_model=Image,
    owner_field_name='uploaded_by_user'
)
