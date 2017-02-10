from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class WagtailSettingsAppConfig(AppConfig):
    name = 'wagtail.contrib.settings'
    label = 'wagtailsettings'
    verbose_name = "Wagtail site settings"
