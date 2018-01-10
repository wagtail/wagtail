from django.apps import AppConfig

from .finders import get_finders


class WagtailEmbedsAppConfig(AppConfig):
    name = 'wagtail.embeds'
    label = 'wagtailembeds'
    verbose_name = "Wagtail embeds"

    def ready(self):
        # Check configuration on startup
        get_finders()
