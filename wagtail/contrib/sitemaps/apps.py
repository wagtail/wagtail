from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailSitemapsAppConfig(AppConfig):
    name = 'wagtail.contrib.sitemaps'
    label = 'wagtailsitemaps'
    verbose_name = _("Wagtail sitemaps")
