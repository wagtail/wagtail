from warnings import warn

from django.conf import settings

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
