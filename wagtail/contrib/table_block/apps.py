from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailTableBlockAppConfig(AppConfig):
    name = "wagtail.contrib.table_block"
    label = "wagtailtableblock"
    verbose_name = _("Wagtail table block")
