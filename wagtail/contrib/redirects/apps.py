from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailRedirectsAppConfig(AppConfig):
    name = 'wagtail.contrib.redirects'
    label = 'wagtailredirects'
    verbose_name = _("Wagtail redirects")
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        from wagtail.core.signals import page_slug_changed, post_page_move

        from .signal_handlers import create_redirects_on_page_move, create_redirects_on_slug_change
        page_slug_changed.connect(create_redirects_on_slug_change)
        post_page_move.connect(create_redirects_on_page_move)
