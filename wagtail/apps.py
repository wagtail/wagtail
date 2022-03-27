from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailAppConfig(AppConfig):
    name = "wagtail"
    label = "wagtailcore"
    verbose_name = _("Wagtail core")
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from wagtail.signal_handlers import register_signal_handlers

        register_signal_handlers()

        from wagtail import widget_adapters  # noqa
