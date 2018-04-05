from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class WagtailTestsAppConfig(AppConfig):
    name = 'wagtail.tests.modeladmintest'
    label = 'test_modeladmintest'
    verbose_name = _("Test Wagtail Model Admin")
