from django.apps import AppConfig, apps
from django.utils.translation import gettext_lazy as _


class WagtailLocalesAppConfig(AppConfig):
    name = "wagtail.locales"
    label = "wagtaillocales"
    verbose_name = _("Wagtail locales")

    def ready(self):
        if apps.is_installed("wagtail.api.v3"):
            from wagtail.api.v3.api import api

            from .api.v3 import router

            api.add_router("/locales/", router)
