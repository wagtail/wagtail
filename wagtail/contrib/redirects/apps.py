from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class WagtailRedirectsAppConfig(AppConfig):
    name = 'wagtail.contrib.redirects'
    label = 'wagtailredirects'
    verbose_name = _("Wagtail redirects")
