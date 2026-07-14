from enum import Enum
from typing import cast

from django.http import HttpRequest

from wagtail.api.v2.querysets import get_public_pages_queryset
from wagtail.models import Page
from wagtail.permission_policies.pages import PagePermissionPolicy
from wagtail.permissions import policy_registry


class AccessTier(str, Enum):
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"


def get_pages_queryset(request: HttpRequest, tier: AccessTier = AccessTier.PUBLIC):
    """
    Return the page queryset for the given access tier.

    PUBLIC: live pages scoped to the site, with handling of view restrictions for authenticated requests.

    AUTHENTICATED: pages the current user can explore in the admin (for admin API tier; not wired to public endpoints yet).
    """
    if tier == AccessTier.PUBLIC:
        return get_public_pages_queryset(request)

    if tier == AccessTier.AUTHENTICATED:
        permission_policy = cast(
            PagePermissionPolicy,
            policy_registry.get_by_type(Page),
        )
        return permission_policy.explorable_instances(request.user)
