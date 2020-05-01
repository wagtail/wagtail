from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailSearchTestsAppConfig(AppConfig):
    name = 'wagtail.tests.search'
    label = 'searchtests'
    verbose_name = _("Wagtail search tests")
