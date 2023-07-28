from warnings import warn

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from wagtail.utils.deprecation import RemovedInWagtail60Warning


class WagtailModelAdminAppConfig(AppConfig):
    name = "wagtail.contrib.modeladmin"
    label = "wagtailmodeladmin"
    verbose_name = _("Wagtail ModelAdmin")

    def ready(self):
        warn(
            "wagtail.contrib.modeladmin is deprecated. "
            "Use wagtail.snippets or the separate wagtail-modeladmin package instead.",
            category=RemovedInWagtail60Warning,
        )
