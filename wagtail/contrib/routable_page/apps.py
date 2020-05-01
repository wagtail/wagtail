from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailRoutablePageAppConfig(AppConfig):
    name = 'wagtail.contrib.routable_page'
    label = 'wagtailroutablepage'
    verbose_name = _("Wagtail routablepage")
