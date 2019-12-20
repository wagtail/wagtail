from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class WagtailFormsAppConfig(AppConfig):
    name = 'wagtail.contrib.forms'
    label = 'wagtailforms'
    verbose_name = _("Wagtail forms")
