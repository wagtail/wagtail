from django.apps import AppConfig

from . import checks  # NOQA


class WagtailAdminAppConfig(AppConfig):
    name = 'wagtail.admin'
    label = 'wagtailadmin'
    verbose_name = "Wagtail admin"
