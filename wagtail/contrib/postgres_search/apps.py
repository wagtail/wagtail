import warnings

from django.apps import AppConfig
from django.core.checks import Error, Tags, register

from wagtail.utils.deprecation import RemovedInWagtail217Warning

from .utils import get_postgresql_connections, set_weights


class PostgresSearchConfig(AppConfig):
    name = 'wagtail.contrib.postgres_search'
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):

        warnings.warn('The wagtail.contrib.postgres_search app will be deprecated in a future release. Please update your search backend to \'wagtail.search.backends.database\', which will pick up a Postgres backend automatically.', RemovedInWagtail217Warning)

        @register(Tags.compatibility, Tags.database)
        def check_if_postgresql(app_configs, **kwargs):
            if get_postgresql_connections():
                return []
            return [Error('You must use a PostgreSQL database '
                          'to use PostgreSQL search.',
                          id='wagtail.contrib.postgres_search.E001')]

        set_weights()

        from .models import IndexEntry
        IndexEntry.add_generic_relations()
