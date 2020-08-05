from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailTestsAppConfig(AppConfig):
    name = 'wagtail.tests.modeladmintest'
    label = 'modeladmintest'
    verbose_name = _("Test Wagtail Model Admin")
