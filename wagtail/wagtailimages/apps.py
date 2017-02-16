from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig

from . import checks  # NOQA


class WagtailImagesAppConfig(AppConfig):
    name = 'wagtail.wagtailimages'
    label = 'wagtailimages'
    verbose_name = "Wagtail images"

    def ready(self):
        from wagtail.wagtailimages.signal_handlers import register_signal_handlers
        register_signal_handlers()
