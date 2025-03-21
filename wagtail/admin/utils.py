import re
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit, urlunsplit

from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.utils.translation import gettext


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
        result = obj.specific_deferred.get_admin_display_title()
    elif isinstance(obj, DraftStateMixin) and obj.latest_revision:
        result = obj.latest_revision.object_str
    else:
        result = str(obj)

    if result.strip() == "":
        result = gettext("%(classname)s object (%(id)s)") % {
            "classname": obj.__class__.__name__,
            "id": obj.pk,
        }

    return result


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


def set_query_params(url: str, params: dict):
    """
    Given a URL and a dictionary of query parameters,
    returns a new URL with those query parameters added or updated.

    If the value of a query parameter is None, that parameter will be removed from the URL.
    """

    scheme, netloc, path, query, fragment = urlsplit(url)
    querydict = parse_qs(query)
    querydict.update(params)
    querydict = {key: value for key, value in querydict.items() if value is not None}
    query = urlencode(querydict, doseq=True)
    return urlunsplit((scheme, netloc, path, query, fragment))


def get_keyboard_key_labels_from_request(request):
    """
    Returns an instance of SimpleNamespace based on the user's keyboard layout
    based on the User-Agent header in the request.

    These are intentionally not translated, as they are key labels that are assumed
    to be consistent across all languages.
    """

    user_agent = request.headers.get("User-Agent", "")
    is_mac_os = re.search(r"Mac|iPod|iPhone|iPad", user_agent)

    labels = {
        "ALT": "⌥" if is_mac_os else "Alt",
        "CMD": "⌘" if is_mac_os else "Ctrl",
        "CTRL": "^" if is_mac_os else "Ctrl",
        "DEL": "Delete",
        "ENTER": "Return" if is_mac_os else "Enter",
        "ESC": "Esc",
        "MOD": "⌘" if is_mac_os else "Ctrl",
        "SHIFT": "Shift",
        "TAB": "Tab",
    }

    return SimpleNamespace(**labels)
