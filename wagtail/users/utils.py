from urllib.parse import parse_qs, urlparse, urlunparse

from django.conf import settings
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _

from wagtail.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME
from wagtail.coreutils import safe_md5

delete_user_perm = "{}.delete_{}".format(
    AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower()
)


def user_can_delete_user(current_user, user_to_delete):
    if not current_user.has_perm(delete_user_perm):
        return False

    if current_user == user_to_delete:
        # users may not delete themselves
        return False

    if user_to_delete.is_superuser and not current_user.is_superuser:
        # ordinary users may not delete superusers
        return False

    return True


def get_gravatar_url(email, size=50, default_params={"d": "mp"}):
    """
    See https://gravatar.com/site/implement/images/ for Gravatar image options.

    Example usage:

    .. code-block:: python

        # Basic usage
        gravatar_url = get_gravatar_url('user@example.com')

        # Customize size and default image
        gravatar_url = get_gravatar_url(
            'user@example.com',
            size=100,
            default_params={'d': 'robohash', 'f': 'y'}
        )

    Note:
        If any parameter in ``default_params`` also exists in the provider URL,
        it will be overridden by the provider URL's query parameter.
    """

    gravatar_provider_url = getattr(
        settings, "WAGTAIL_GRAVATAR_PROVIDER_URL", "//www.gravatar.com/avatar"
    )

    if (not email) or (gravatar_provider_url is None):
        return None

    parsed_url = urlparse(gravatar_provider_url)

    params = {
        **default_params,
        **(parse_qs(parsed_url.query or "")),
        # requested at retina size by default and scaled down at point of use with css
        "s": int(size) * 2,
    }

    email_hash = safe_md5(
        email.lower().encode("utf-8"), usedforsecurity=False
    ).hexdigest()

    parsed_url = parsed_url._replace(
        path=f"{parsed_url.path.rstrip('/')}/{email_hash}",
        query=urlencode(params, doseq=True),
    )

    gravatar_url = urlunparse(parsed_url)

    return gravatar_url


def get_deleted_user_display_name(user_id):
    # Use a string placeholder as the user id could be non-numeric
    return _("user %(id)s (deleted)") % {"id": user_id}
