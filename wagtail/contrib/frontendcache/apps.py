from django.apps import AppConfig
from wagtail.contrib.frontendcache.signal_handlers import register_signal_handlers


class WagtailFrontendCacheAppConfig(AppConfig):
    name = 'wagtail.contrib.frontendcache'
    label = 'wagtailfrontendcache'
    verbose_name = "Wagtail frontend cache"

    def ready(self):
        register_signal_handlers()
