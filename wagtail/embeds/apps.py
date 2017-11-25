from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig

from .finders import get_finders


class WagtailEmbedsAppConfig(AppConfig):
    name = 'wagtail.embeds'
    label = 'wagtailembeds'
    verbose_name = "Wagtail embeds"

    def ready(self):
        # Check configuration on startup
        get_finders()
