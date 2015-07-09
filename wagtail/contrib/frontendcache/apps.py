from django.apps import AppConfig


class WagtailFrontendCacheAppConfig(AppConfig):
    name = 'wagtail.contrib.frontendcache'
    label = 'wagtailfrontendcache'
    verbose_name = "Wagtail frontend cache"

    def ready(self):
        from .signal_handlers import register_signal_handlers
        register_signal_handlers()
