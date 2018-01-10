from django.apps import AppConfig

from wagtail.contrib.frontend_cache.signal_handlers import register_signal_handlers


class WagtailFrontendCacheAppConfig(AppConfig):
    name = 'wagtail.contrib.frontend_cache'
    label = 'wagtailfrontendcache'
    verbose_name = "Wagtail frontend cache"

    def ready(self):
        register_signal_handlers()
