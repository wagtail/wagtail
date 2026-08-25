import warnings

from wagtail.contrib.redirects.models import Redirect
from wagtail.permissions import policy_registry
from wagtail.utils.deprecation import RemovedInWagtail90Warning

warnings.warn(
    "wagtail.contrib.redirects.permissions.permission_policy is deprecated. "
    "Use wagtail.permissions.policy_registry.get_by_type(Redirect) instead.",
    RemovedInWagtail90Warning,
    stacklevel=2,
)
# Do not use a fallback here, as it would prevent the real permission policy
# from being registered if there is code that imports this module before the
# app's ready() is called.
permission_policy = policy_registry.get_by_type(Redirect, fallback=False)
if not permission_policy:
    from wagtail.permission_policies import ModelPermissionPolicy

    permission_policy = ModelPermissionPolicy(Redirect)
    warnings.warn(
        "wagtail.contrib.redirects.permissions was imported before "
        "wagtail.contrib.redirects app is ready. Avoid importing "
        "wagtail.contrib.redirects.permissions at the module level.",
        RuntimeWarning,
        stacklevel=2,
    )
