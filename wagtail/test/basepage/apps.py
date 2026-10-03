from django.apps import AppConfig


class BasepageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "wagtail.test.basepage"
    label = "basepage"
