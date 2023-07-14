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

    email_bytes = email.lower().encode("utf-8")
    hash = safe_md5(email_bytes, usedforsecurity=False).hexdigest()
    gravatar_url = "{gravatar_provider_url}/{hash}?{params}".format(
        gravatar_provider_url=gravatar_provider_url.rstrip("/"),
        hash=hash,
        params=urlencode({"s": size, "d": default}),
    )

    return gravatar_url


def get_deleted_user_display_name(user_id):
    # Use a string placeholder as the user id could be non-numeric
    return _("user %(id)s (deleted)") % {"id": user_id}
