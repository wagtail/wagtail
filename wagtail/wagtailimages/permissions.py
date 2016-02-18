from wagtail.wagtailcore.permission_policies import OwnershipPermissionPolicy
from wagtail.wagtailimages.models import Image, get_image_model


permission_policy = OwnershipPermissionPolicy(
    get_image_model(),
    auth_model=Image,
    owner_field_name='uploaded_by_user'
)
