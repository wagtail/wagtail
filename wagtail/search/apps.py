from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from wagtail.search.signal_handlers import register_signal_handlers


class WagtailSearchAppConfig(AppConfig):
    name = 'wagtail.search'
    label = 'wagtailsearch'
    verbose_name = _("Wagtail search")

    def ready(self):
        register_signal_handlers()
