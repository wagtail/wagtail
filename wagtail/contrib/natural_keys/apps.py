"""
App configuration for Wagtail natural keys.
"""

from django.apps import AppConfig


class NaturalKeysConfig(AppConfig):
    name = 'wagtail.contrib.natural_keys'
    verbose_name = 'Wagtail Natural Keys'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        """Set up natural key support when the app is ready"""
        from . import natural_keys  