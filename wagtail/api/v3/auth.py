from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from ninja.security import HttpBearer
from ninja.security.http import HttpAuthBase

from wagtail.models import APIToken


class BearerTokenAuth(HttpBearer):
    """
    Resolves ``Authorization: Bearer <token>`` against APIToken digests.
    Returns the APIToken (Ninja assigns it to ``request.auth``) and sets
    ``request.user``. Projects may subclass this to customize resolution.
    """

    def authenticate(self, request, token: str):
        try:
            api_token = APIToken.objects.select_related("user").get(
                key_hash__in=APIToken.candidate_key_hashes(token),
                revoked_at__isnull=True,
            )
        except APIToken.DoesNotExist:
            user = None
        else:
            user = api_token.user

        # is_active may be a plain class attribute (AbstractBaseUser) rather
        # than a database field, so check in Python instead of the queryset.
        if not (user and user.is_active):
            user = AnonymousUser()

        # Normalize request.user to an anonymous user if the token is invalid or
        # the user is inactive, overwriting Django auth backends e.g. session.
        request.user = user
        if not request.user.is_authenticated:
            return None

        self._touch_last_used(api_token)
        return api_token

    def _touch_last_used(self, api_token):
        interval = getattr(settings, "WAGTAILAPI_TOKEN_LAST_USED_INTERVAL", 60)
        if interval is None:
            return
        now = timezone.now()
        if (
            api_token.last_used_at is None
            or (now - api_token.last_used_at).total_seconds() >= interval
        ):
            APIToken.objects.filter(pk=api_token.pk).update(last_used_at=now)


class AllowAnonymous(HttpAuthBase):
    """Fallback auth callback marking a request as explicitly anonymous.

    Use after BearerTokenAuth on public-read endpoints:
    ``auth=[BearerTokenAuth(), AllowAnonymous()]``.

    Like BearerTokenAuth, this also normalizes ``request.user`` so a Django
    session cookie cannot elevate the request.
    """

    def __call__(self, request):
        request.user = AnonymousUser()
        return request.user
