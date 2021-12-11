from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class WagtailRedirectsAppConfig(AppConfig):
    name = 'wagtail.contrib.redirects'
    label = 'wagtailredirects'
    verbose_name = _("Wagtail redirects")
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        from wagtail.core.signals import page_url_path_changed

        from .signal_handlers import autocreate_redirects
        if getattr(settings, "WAGTAILREDIRECTS_AUTOCREATE", False):
            page_url_path_changed.connect(autocreate_redirects)
