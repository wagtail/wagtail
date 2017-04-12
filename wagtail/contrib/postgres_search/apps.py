from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig
from django.core.checks import Error, Tags, register

from .utils import (
    BOOSTS_WEIGHTS, WEIGHTS_COUNT, WEIGHTS_VALUES, determine_boosts_weights,
    get_postgresql_connections)


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
        sorted_boosts_weights = sorted(BOOSTS_WEIGHTS, key=lambda t: t[0])
        max_weight = sorted_boosts_weights[-1][0]
        WEIGHTS_VALUES.extend([v / max_weight
                               for v, w in sorted_boosts_weights])
        for _ in range(WEIGHTS_COUNT - len(WEIGHTS_VALUES)):
            WEIGHTS_VALUES.insert(0, 0)
