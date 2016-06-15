from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig

from wagtail.wagtailsearch.signal_handlers import register_signal_handlers


class WagtailSearchAppConfig(AppConfig):
    name = 'wagtail.wagtailsearch'
    label = 'wagtailsearch'
    verbose_name = "Wagtail search"

    def ready(self):
        register_signal_handlers()
