from django.apps import AppConfig


class WagtailTestCustomUserAppConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "wagtail.test.customuser"
    label = "customuser"
