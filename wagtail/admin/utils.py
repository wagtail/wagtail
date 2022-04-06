from warnings import warn

from django.conf import settings

from wagtail.utils.deprecation import RemovedInWagtail50Warning


def get_admin_base_url(context=None):
    """
    Gets the base URL for the wagtail admin site. This is set in `settings.WAGTAILADMIN_BASE_URL`,
    which was previously `settings.BASE_URL`.
    If setting is omitted and this is called in a request context, falls back to
    `request.site.root_url` or next the host_name of the request.
    """

    admin_base_url = getattr(settings, "WAGTAILADMIN_BASE_URL", None)
    if admin_base_url is None and hasattr(settings, "BASE_URL"):
        warn(
            "settings.BASE_URL has been renamed to settings.WAGTAILADMIN_BASE_URL",
            category=RemovedInWagtail50Warning,
        )
        admin_base_url = settings.BASE_URL

    if admin_base_url is None and context is not None:
        request = context["request"]
        admin_base_url = getattr(request.site, "root_url", None)
        if admin_base_url is None:
            admin_base_url = request.get_host()
            secure_prefix = "http"
            if request.is_secure():
                secure_prefix = "https"
            admin_base_url = secure_prefix + "://" + admin_base_url

    return admin_base_url
