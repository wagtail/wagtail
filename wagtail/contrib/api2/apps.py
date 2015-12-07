import warnings

from django.apps import AppConfig, apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from wagtail.utils.deprecation import RemovedInWagtail14Warning


class WagtailAPI2AppConfig(AppConfig):
    name = 'wagtail.contrib.api2'
    label = 'wagtailapi_v2'
    verbose_name = "Wagtail API v2"

    def ready(self):
        # Install cache purging signal handlers
        if getattr(settings, 'WAGTAILAPI_USE_FRONTENDCACHE', False):
            if apps.is_installed('wagtail.contrib.wagtailfrontendcache'):
                from wagtail.contrib.api2.signal_handlers import register_signal_handlers
                register_signal_handlers()
            else:
                raise ImproperlyConfigured("The setting 'WAGTAILAPI_USE_FRONTENDCACHE' is True but 'wagtail.contrib.wagtailfrontendcache' is not in INSTALLED_APPS.")

        if not apps.is_installed('rest_framework'):
            warnings.warn(
                "The 'api2' module now requires 'rest_framework' to be installed. "
                "Please add 'rest_framework' to INSTALLED_APPS.",
                RemovedInWagtail14Warning)
