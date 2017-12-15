from django.apps import AppConfig


class WagtailCoreAppConfig(AppConfig):
    name = 'wagtail.core'
    label = 'wagtailcore'
    verbose_name = "Wagtail core"

    def ready(self):
        from wagtail.core.rich_text import register_rich_text_handlers
        from wagtail.core.signal_handlers import register_signal_handlers
        register_rich_text_handlers()
        register_signal_handlers()
