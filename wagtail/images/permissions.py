import warnings

from wagtail.images import get_image_model
from wagtail.permissions import policies_registry
from wagtail.utils.deprecation import RemovedInWagtail90Warning

warnings.warn(
    "wagtail.images.permissions.permission_policy is deprecated. "
    "Use wagtail.permissions.policies_registry.get_by_type(get_image_model()) instead.",
    RemovedInWagtail90Warning,
)
permission_policy = policies_registry.get_by_type(get_image_model())
