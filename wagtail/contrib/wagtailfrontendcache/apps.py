from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig

from wagtail.contrib.wagtailfrontendcache.signal_handlers import register_signal_handlers


class WagtailFrontendCacheAppConfig(AppConfig):
    name = 'wagtail.contrib.wagtailfrontendcache'
    label = 'wagtailfrontendcache'
    verbose_name = "Wagtail frontend cache"

    def ready(self):
        register_signal_handlers()
