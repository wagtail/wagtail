from http import HTTPStatus
from typing import cast

import swapper
from django.http import HttpRequest
from ninja.errors import HttpError

from wagtail.api.querysets import get_public_pages_queryset
from wagtail.permission_policies.pages import PagePermissionPolicy
from wagtail.permissions import policy_registry

Page = swapper.load_model("wagtailcore", "Page")


def get_pages_queryset(request: HttpRequest, model=Page):
    """
    Return the page queryset for the given access tier.

    PUBLIC: live pages scoped to the site, with handling of view restrictions for authenticated requests.

    AUTHENTICATED: pages the current user can explore in the admin (for admin API tier; not wired to public endpoints yet).
    """
    if not request.user.is_authenticated:
        try:
            queryset = get_public_pages_queryset(request, model)
        except ValueError as e:  # ?site= filter returned multiple sites
            raise HttpError(HTTPStatus.BAD_REQUEST, str(e)) from e

    else:
        permission_policy = cast(
            PagePermissionPolicy,
            policy_registry.get_by_type(Page),
        )

        if model is not Page and model is not permission_policy.model:
            # A single page type has been specified, and the registered policy
            # is not specific to that page type (e.g. the default policy or a
            # custom one registered for the base page model). Re-instantiate the
            # policy with the specific page type so we can get the specific
            # queryset to use for filtering.

            # Alternatively, we could use the base page's policy to get
            # explorable_instances(), and use it as a pk__in= filter for the
            # specific queryset (i.e. V2 behavior), but that is inefficient.
            permission_policy = permission_policy.for_model(model)

        queryset = permission_policy.explorable_instances(request.user)

    return queryset.select_related("content_type", "locale").order_by("pk")
