import warnings

from wagtail.contrib.redirects.models import Redirect
from wagtail.permissions import policies_registry
from wagtail.utils.deprecation import RemovedInWagtail90Warning

warnings.warn(
    "wagtail.contrib.redirects.permissions.permission_policy is deprecated. "
    "Use wagtail.permissions.policies_registry.get_by_type(Redirect) instead.",
    RemovedInWagtail90Warning,
)
permission_policy = policies_registry.get_by_type(Redirect)
