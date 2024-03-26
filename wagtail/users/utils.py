from django.conf import settings
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
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
    """
    Generates a Gravatar URL for the given email with customizable size and default image.
    See https://gravatar.com/site/implement/images/ for Gravatar image options.
    """
    gravatar_provider_url = getattr(
        settings, "WAGTAIL_GRAVATAR_PROVIDER_URL", "//www.gravatar.com/avatar"
    )

    if not email or not gravatar_provider_url:
        return None

    # Set default image type and adjust size for retina displays
    default = "mp"
    size *= 2  # Retina display support

    # Parse the provided URL and extract query parameters
    parsed_url = urlparse(gravatar_provider_url)
    query_params = parse_qs(parsed_url.query)
    email_bytes = email.lower().encode("utf-8")
    email_hash = safe_md5(email_bytes).hexdigest()
    email_hash='/'+ email_hash

    # Merge default parameters with those extracted from the provided URL
    query_params.update({"d": default, "s": str(size)})
    query_string = urlencode(query_params, doseq=True)

    # Rebuild the URL with the merged parameters
    gravatar_url = urlunparse((
        parsed_url.scheme, parsed_url.netloc, parsed_url.path + email_hash, 
        parsed_url.params, query_string, parsed_url.fragment
    ))

    return gravatar_url

def get_deleted_user_display_name(user_id):
    # Use a string placeholder as the user id could be non-numeric
    return _("user %(id)s (deleted)") % {"id": user_id}
