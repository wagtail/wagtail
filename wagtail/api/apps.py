from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig, apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class WagtailAPIAppConfig(AppConfig):
    name = 'wagtail.api'
    label = 'wagtailapi'
    verbose_name = "Wagtail API"

    def ready(self):
        # Install cache purging signal handlers
        if getattr(settings, 'WAGTAILAPI_USE_FRONTENDCACHE', False):
            if apps.is_installed('wagtail.contrib.wagtailfrontendcache'):
                from wagtail.api.v2.signal_handlers import register_signal_handlers as register_signal_handlers_v2
                register_signal_handlers_v2()
            else:
                raise ImproperlyConfigured("The setting 'WAGTAILAPI_USE_FRONTENDCACHE' is True but 'wagtail.contrib.wagtailfrontendcache' is not in INSTALLED_APPS.")
