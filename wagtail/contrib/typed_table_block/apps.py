from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailTableBlockAppConfig(AppConfig):
    name = "wagtail.contrib.typed_table_block"
    label = "wagtailtypedtableblock"
    verbose_name = _("Wagtail typed table block")
    default_auto_field = "django.db.models.AutoField"
