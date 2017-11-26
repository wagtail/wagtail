from django.apps import AppConfig

from . import checks  # NOQA


class WagtailAdminAppConfig(AppConfig):
    name = 'wagtail.wagtailadmin'
    label = 'wagtailadmin'
    verbose_name = "Wagtail admin"
