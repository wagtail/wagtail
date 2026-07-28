from enum import Enum

from django.http import HttpRequest

from wagtail.api.v2.querysets import get_public_pages_queryset
from wagtail.models import Page
from wagtail.permissions import page_permission_policy


class AccessTier(str, Enum):
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"


def get_pages_queryset(
    request: HttpRequest, tier: AccessTier = AccessTier.PUBLIC, model=Page
):
    """
    Return the page queryset for the given access tier.

    PUBLIC: live pages scoped to the site, with handling of view restrictions for authenticated requests.

    AUTHENTICATED: pages the current user can explore in the admin (for admin API tier; not wired to public endpoints yet).
    """
    if tier == AccessTier.PUBLIC:
        return get_public_pages_queryset(request, model)

    if tier == AccessTier.AUTHENTICATED:
        queryset = page_permission_policy.explorable_instances(request.user)
        if model is not Page:
            # If a single page type has been specified, swap out the Page-based
            # queryset for one based on the specific page model so that we can
            # filter on any custom APIFields defined on that model.
            queryset = model._default_manager.filter(
                pk__in=queryset.values_list("pk", flat=True)
            )
        return queryset
