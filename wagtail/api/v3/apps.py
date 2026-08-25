from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailAPIV3AppConfig(AppConfig):
    name = "wagtail.api.v3"
    label = "wagtailapi_v3"
    verbose_name = _("Wagtail API v3")

    def ready(self):
        from wagtail.api.rich_text import APIRichText

        APIRichText.check_setting()
