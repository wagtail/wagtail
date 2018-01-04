from django.apps import AppConfig

from . import checks  # NOQA


class WagtailSettingsAppConfig(AppConfig):
    name = 'wagtail.contrib.settings'
    label = 'wagtailsettings'
    verbose_name = "Wagtail site settings"
