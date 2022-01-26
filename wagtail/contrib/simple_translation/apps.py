from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SimpleTranslationAppConfig(AppConfig):
    name = "wagtail.contrib.simple_translation"
    label = "simple_translation"
    verbose_name = _("Wagtail simple translation")
    default_auto_field = 'django.db.models.AutoField'
