from django.apps import AppConfig
from django.db import connection
from django.core.exceptions import ImproperlyConfigured


class WagtailPostgresSearchAppConfig(AppConfig):
    name = 'wagtail.contrib.wagtailpostgressearch'
    label = 'wagtailpostgressearch'
    verbose_name = "Wagtail Postgres search"

    def ready(self):
        if connection.vendor != 'postgresql':
            raise ImproperlyConfigured("Use postgres")
