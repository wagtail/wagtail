from django.apps import AppConfig


class WagtailSettingsAppConfig(AppConfig):
    name = "wagtail.contrib.settings"
    label = "wagtailsettings"
    verbose_name = "Wagtail settings"
    default_auto_field = "django.db.models.AutoField"
