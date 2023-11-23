from wagtail.images import get_image_model
from wagtail.permissions import policies_registry as policies

# This is deprecated, but kept for backwards compatibility
# The policy should be retrieved using `policies.get_by_type(get_image_model())`
# TODO: Add deprecation warning
permission_policy = policies.get_by_type(get_image_model())
