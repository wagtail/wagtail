from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailRedirectsAppConfig(AppConfig):
    name = "wagtail.contrib.redirects"
    label = "wagtailredirects"
    verbose_name = _("Wagtail redirects")
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from wagtail.signals import page_slug_changed, post_page_move

        from .signal_handlers import (
            autocreate_redirects_on_page_move,
            autocreate_redirects_on_slug_change,
        )

        post_page_move.connect(autocreate_redirects_on_page_move)
        page_slug_changed.connect(autocreate_redirects_on_slug_change)
