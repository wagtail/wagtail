from django.apps import AppConfig, apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _


class WagtailAPIV2AppConfig(AppConfig):
    name = 'wagtail.api.v2'
    label = 'wagtailapi_v2'
    verbose_name = _("Wagtail API v2")

    def ready(self):
        # Install cache purging signal handlers
        if getattr(settings, 'WAGTAILAPI_USE_FRONTENDCACHE', False):
            if apps.is_installed('wagtail.contrib.frontend_cache'):
                from wagtail.api.v2.signal_handlers import register_signal_handlers
                register_signal_handlers()
            else:
                raise ImproperlyConfigured("The setting 'WAGTAILAPI_USE_FRONTENDCACHE' is True but 'wagtail.contrib.frontend_cache' is not in INSTALLED_APPS.")
