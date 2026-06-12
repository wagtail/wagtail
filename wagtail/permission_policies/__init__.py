from django.conf import settings
from .base import *  # NOQA: F403

def override_permission_policy(policy: str, default):
    """
    Override permission policy from settings
    """
    permission_policy_overrides = getattr(settings, "WAGTAIL_PERMISSION_POLICY_OVERRIDES", {})
    permission_policy = permission_policy_overrides.get(policy)
    if permission_policy:
        return permission_policy
    return default
     