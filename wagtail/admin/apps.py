from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from . import checks  # NOQA


class WagtailAdminAppConfig(AppConfig):
    name = 'wagtail.admin'
    label = 'wagtailadmin'
    verbose_name = _("Wagtail admin")

    def ready(self):
        from wagtail.admin.signal_handlers import register_signal_handlers
        register_signal_handlers()
