from django.apps import AppConfig
from django.db import connection
from django.utils.translation import gettext_lazy as _

from wagtail.search.signal_handlers import register_signal_handlers


class WagtailSearchAppConfig(AppConfig):
    name = 'wagtail.search'
    label = 'wagtailsearch'
    verbose_name = _("Wagtail search")
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        register_signal_handlers()

        if connection.vendor == 'postgresql':
            # Only PostgreSQL has support for tsvector weights
            from wagtail.search.backends.database.postgres.weights import set_weights
            set_weights()

        from wagtail.search.models import IndexEntry
        IndexEntry.add_generic_relations()
