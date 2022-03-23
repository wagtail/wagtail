import hashlib

from django.conf import settings
from django.utils.http import urlencode

from wagtail.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME

delete_user_perm = "{0}.delete_{1}".format(
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


def get_gravatar_url(email, size=50):
    default = "mm"
    size = (
        int(size) * 2
    )  # requested at retina size by default and scaled down at point of use with css
    gravatar_provider_url = getattr(
        settings, "WAGTAIL_GRAVATAR_PROVIDER_URL", "//www.gravatar.com/avatar"
    )

    if (not email) or (gravatar_provider_url is None):
        return None

    gravatar_url = "{gravatar_provider_url}/{hash}?{params}".format(
        gravatar_provider_url=gravatar_provider_url.rstrip("/"),
        hash=hashlib.md5(email.lower().encode("utf-8")).hexdigest(),
        params=urlencode({"s": size, "d": default}),
    )

    return gravatar_url
