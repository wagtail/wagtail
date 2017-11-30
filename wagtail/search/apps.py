from django.apps import AppConfig

from wagtail.search.signal_handlers import register_signal_handlers


class WagtailSearchAppConfig(AppConfig):
    name = 'wagtail.search'
    label = 'wagtailsearch'
    verbose_name = "Wagtail search"

    def ready(self):
        register_signal_handlers()
