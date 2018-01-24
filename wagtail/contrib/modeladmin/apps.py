from django.apps import AppConfig

from . import checks  # NOQA


class WagtailModelAdminAppConfig(AppConfig):
    name = 'wagtail.contrib.modeladmin'
    label = 'wagtailmodeladmin'
    verbose_name = "Wagtail ModelAdmin"
