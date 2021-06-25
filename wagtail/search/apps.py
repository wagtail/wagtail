from django.apps import AppConfig, apps
from django.utils.translation import gettext_lazy as _

from wagtail.search.signal_handlers import register_signal_handlers

from .utils import set_weights


class WagtailSearchAppConfig(AppConfig):
    name = 'wagtail.search'
    label = 'wagtailsearch'
    verbose_name = _("Wagtail search")
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        register_signal_handlers()

        set_weights()

        if not apps.is_installed('wagtail.contrib.postgres_search'):
            # We shall not add the generic relations if they have already been added by the legacy postgres_search app (doing so would duplicate the relationships)
            # TODO: When the concrete IndexEntry models are available we should, add the generic relations here
            pass
