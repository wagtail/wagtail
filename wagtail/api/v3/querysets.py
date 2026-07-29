from enum import Enum
from http import HTTPStatus

from django.http import HttpRequest
from ninja.errors import HttpError

from wagtail.api.querysets import get_public_pages_queryset
from wagtail.models import Page
from wagtail.permission_policies.pages import PagePermissionPolicy


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
        try:
            queryset = get_public_pages_queryset(request, model)
        except ValueError as e:  # ?site= filter returned multiple sites
            raise HttpError(HTTPStatus.BAD_REQUEST, str(e)) from e

    if tier == AccessTier.AUTHENTICATED:
        # FIXME: When the registry is used, and a specific page model is passed,
        # how do we ensure the policy returns a queryset of that model (not Page)?
        # If the registered policy's model is not the same as the passed model
        # (e.g. the default), we may have to resort to instantiating a new instance.
        # Alternatively, we could use the base page's policy to get
        # explorable_instances(), and then use it as a pk__in= filter using the
        # specific model's queryset (i.e. V2 behavior), but this is inefficient.
        queryset = PagePermissionPolicy(model).explorable_instances(request.user)
    return queryset.select_related("content_type", "locale")
