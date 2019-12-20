from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class WagtailCoreAppConfig(AppConfig):
    name = 'wagtail.core'
    label = 'wagtailcore'
    verbose_name = _("Wagtail core")

    def ready(self):
        from wagtail.core.signal_handlers import register_signal_handlers
        register_signal_handlers()
