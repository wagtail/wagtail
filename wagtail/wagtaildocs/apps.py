from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class WagtailDocsAppConfig(AppConfig):
    name = 'wagtail.wagtaildocs'
    label = 'wagtaildocs'
    verbose_name = "Wagtail documents"

    def ready(self):
        from wagtail.wagtaildocs.signal_handlers import register_signal_handlers
        register_signal_handlers()
