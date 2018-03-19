from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class WagtailStyleGuideAppConfig(AppConfig):
    name = 'wagtail.contrib.styleguide'
    label = 'wagtailstyleguide'
    verbose_name = _("Wagtail style guide")
