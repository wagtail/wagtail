from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from wagtail.search.signal_handlers import register_signal_handlers

from .utils import set_weights


class WagtailSearchAppConfig(AppConfig):
    name = 'wagtail.search'
    label = 'wagtailsearch'
    verbose_name = _("Wagtail search")
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        register_signal_handlers()

        set_weights()
