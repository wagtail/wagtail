from enum import Enum

from django.http import HttpRequest

from wagtail.api.v2.querysets import get_public_pages_queryset
from wagtail.permissions import page_permission_policy


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
        return page_permission_policy.explorable_instances(getattr(request, "user"))
