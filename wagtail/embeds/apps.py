from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from .finders import get_finders


class WagtailEmbedsAppConfig(AppConfig):
    name = 'wagtail.embeds'
    label = 'wagtailembeds'
    verbose_name = _("Wagtail embeds")

    def ready(self):
        # Check configuration on startup
        get_finders()
