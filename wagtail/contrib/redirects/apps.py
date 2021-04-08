from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailRedirectsAppConfig(AppConfig):
    name = 'wagtail.contrib.redirects'
    label = 'wagtailredirects'
    verbose_name = _("Wagtail redirects")
    default_auto_field = 'django.db.models.AutoField'
