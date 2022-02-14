from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailStyleGuideAppConfig(AppConfig):
    name = "wagtail.contrib.styleguide"
    label = "wagtailstyleguide"
    verbose_name = _("Wagtail style guide")
