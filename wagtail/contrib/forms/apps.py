from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailFormsAppConfig(AppConfig):
    name = "wagtail.contrib.forms"
    label = "wagtailforms"
    verbose_name = _("Wagtail forms")
    default_auto_field = "django.db.models.AutoField"
