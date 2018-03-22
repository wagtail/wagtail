from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from . import checks  # NOQA


class WagtailImagesAppConfig(AppConfig):
    name = 'wagtail.images'
    label = 'wagtailimages'
    verbose_name = _("Wagtail images")

    def ready(self):
        from wagtail.images.signal_handlers import register_signal_handlers
        register_signal_handlers()
