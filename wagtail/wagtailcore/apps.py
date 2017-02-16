from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class WagtailCoreAppConfig(AppConfig):
    name = 'wagtail.wagtailcore'
    label = 'wagtailcore'
    verbose_name = "Wagtail core"

    def ready(self):
        from wagtail.wagtailcore.signal_handlers import register_signal_handlers
        register_signal_handlers()
