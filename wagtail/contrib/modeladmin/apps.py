from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class WagtailModelAdminAppConfig(AppConfig):
    name = 'wagtail.contrib.modeladmin'
    label = 'wagtailmodeladmin'
    verbose_name = _("Wagtail ModelAdmin")
