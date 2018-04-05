from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

from . import checks  # NOQA


class WagtailAdminAppConfig(AppConfig):
    name = 'wagtail.admin'
    label = 'wagtailadmin'
    verbose_name = _("Wagtail admin")
