from warnings import warn

from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme

from wagtail.utils.deprecation import RemovedInWagtail50Warning


def get_admin_base_url():
    """
    Gets the base URL for the wagtail admin site. This is set in `settings.WAGTAILADMIN_BASE_URL`,
    which was previously `settings.BASE_URL`.
    """

    admin_base_url = getattr(settings, "WAGTAILADMIN_BASE_URL", None)
    if admin_base_url is None and hasattr(settings, "BASE_URL"):
        warn(
            "settings.BASE_URL has been renamed to settings.WAGTAILADMIN_BASE_URL",
            category=RemovedInWagtail50Warning,
        )
        admin_base_url = settings.BASE_URL

    return admin_base_url


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
