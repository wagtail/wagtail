from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme


def get_admin_base_url():
    """
    Gets the base URL for the wagtail admin site. This is set in `settings.WAGTAILADMIN_BASE_URL`.
    """
    return getattr(settings, "WAGTAILADMIN_BASE_URL", None)


def get_valid_next_url_from_request(request):
    next_url = request.POST.get("next") or request.GET.get("next")
    if not next_url or not url_has_allowed_host_and_scheme(
        url=next_url, allowed_hosts={request.get_host()}
    ):
        return ""
    return next_url


def get_latest_str(obj):
    """
    Helper function to get the latest string representation of an object.
    Draft changes are saved as revisions instead of immediately reflected to the
    instance, so this function utilises the latest revision's object_str
    attribute if available.
    """
    from wagtail.models import DraftStateMixin, Page

    if isinstance(obj, Page):
        return obj.specific_deferred.get_admin_display_title()
    if isinstance(obj, DraftStateMixin) and obj.latest_revision:
        return obj.latest_revision.object_str
    return str(obj)


def get_user_display_name(user):
    """
    Returns the preferred display name for the given user object: the result of
    user.get_full_name() if implemented and non-empty, or user.get_username() otherwise.
    """
    try:
        full_name = user.get_full_name().strip()
        if full_name:
            return full_name
    except AttributeError:
        pass

    try:
        return user.get_username()
    except AttributeError:
        # we were passed None or something else that isn't a valid user object; return
        # empty string to replicate the behaviour of {{ user.get_full_name|default:user.get_username }}
        return ""
