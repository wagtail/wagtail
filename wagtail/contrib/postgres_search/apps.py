from django.apps import AppConfig
from django.core.checks import Error, Tags, register

from .utils import (
    BOOSTS_WEIGHTS, WEIGHTS_VALUES, determine_boosts_weights, get_postgresql_connections)


class PostgresSearchConfig(AppConfig):
    name = 'wagtail.contrib.postgres_search'

    def ready(self):
        @register(Tags.compatibility, Tags.database)
        def check_if_postgresql(app_configs, **kwargs):
            if get_postgresql_connections():
                return []
            return [Error('You must use a PostgreSQL database '
                          'to use PostgreSQL search.',
                          id='wagtail.contrib.postgres_search.E001')]

        BOOSTS_WEIGHTS.extend(determine_boosts_weights())
        max_weight = BOOSTS_WEIGHTS[0][0]
        WEIGHTS_VALUES.extend([v / max_weight
                               for v, w in reversed(BOOSTS_WEIGHTS)])
