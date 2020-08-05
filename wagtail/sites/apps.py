from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailSitesAppConfig(AppConfig):
    name = 'wagtail.sites'
    label = 'wagtailsites'
    verbose_name = _("Wagtail sites")
