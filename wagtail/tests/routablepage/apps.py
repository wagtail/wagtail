from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class WagtailRoutablePageTestsAppConfig(AppConfig):
    name = 'wagtail.tests.routablepage'
    label = 'routablepagetests'
    verbose_name = _("Wagtail routable page tests")
