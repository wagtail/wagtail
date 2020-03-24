from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from wagtail.contrib.frontend_cache.signal_handlers import register_signal_handlers


class WagtailFrontendCacheAppConfig(AppConfig):
    name = 'wagtail.contrib.frontend_cache'
    label = 'wagtailfrontendcache'
    verbose_name = _("Wagtail frontend cache")

    def ready(self):
        register_signal_handlers()
