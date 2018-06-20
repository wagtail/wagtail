from itertools import zip_longest

from django.apps import apps
from django.db import connections

from wagtail.search.index import Indexed, RelatedFields, SearchField

try:
    # Only use the GPLv2 licensed unidecode if it's installed.
    from unidecode import unidecode
except ImportError:
    def unidecode(value):
        return value


def get_postgresql_connections():
    return [connection for connection in connections.all()
            if connection.vendor == 'postgresql']


def get_descendant_models(model):
    """
    Returns all descendants of a model, including the model itself.
    """
    descendant_models = {other_model for other_model in apps.get_models()
                         if issubclass(other_model, model)}
    descendant_models.add(model)
    return descendant_models


def get_content_type_pk(model):
    # We import it locally because this file is loaded before apps are ready.
    from django.contrib.contenttypes.models import ContentType
    return ContentType.objects.get_for_model(model).pk


def get_ancestors_content_types_pks(model):
    """
    Returns content types ids for the ancestors of this model, excluding it.
    """
    from django.contrib.contenttypes.models import ContentType
    return [ct.pk for ct in
            ContentType.objects.get_for_models(*model._meta.get_parent_list())
            .values()]


def get_descendants_content_types_pks(model):
    """
    Returns content types ids for the descendants of this model, including it.
    """
    from django.contrib.contenttypes.models import ContentType
    return [ct.pk for ct in
            ContentType.objects.get_for_models(*get_descendant_models(model))
            .values()]


def get_search_fields(search_fields):
    for search_field in search_fields:
        if isinstance(search_field, SearchField):
            yield search_field
        elif isinstance(search_field, RelatedFields):
            for sub_field in get_search_fields(search_field.fields):
                yield sub_field


WEIGHTS = 'ABCD'
WEIGHTS_COUNT = len(WEIGHTS)
# These are filled when apps are ready.
BOOSTS_WEIGHTS = []
WEIGHTS_VALUES = []


def get_boosts():
    boosts = set()
    for model in apps.get_models():
        if issubclass(model, Indexed):
            for search_field in get_search_fields(model.get_search_fields()):
                boost = search_field.boost
                if boost is not None:
                    boosts.add(boost)
    return boosts


def determine_boosts_weights(boosts=()):
    if not boosts:
        boosts = get_boosts()
    boosts = list(sorted(boosts, reverse=True))
    min_boost = boosts[-1]
    if len(boosts) <= WEIGHTS_COUNT:
        return list(zip_longest(boosts, WEIGHTS, fillvalue=min(min_boost, 0)))
    max_boost = boosts[0]
    boost_step = (max_boost - min_boost) / (WEIGHTS_COUNT - 1)
    return [(max_boost - (i * boost_step), weight)
            for i, weight in enumerate(WEIGHTS)]


def set_weights():
    BOOSTS_WEIGHTS.extend(determine_boosts_weights())
    weights = [w for w, c in BOOSTS_WEIGHTS]
    min_weight = min(weights)
    if min_weight <= 0:
        if min_weight == 0:
            min_weight = -0.1
        weights = [w - min_weight for w in weights]
    max_weight = max(weights)
    WEIGHTS_VALUES.extend([w / max_weight
                           for w in reversed(weights)])


def get_weight(boost):
    if boost is None:
        return WEIGHTS[-1]
    for max_boost, weight in BOOSTS_WEIGHTS:
        if boost >= max_boost:
            return weight
    return weight


def get_sql_weights():
    return '{' + ','.join(map(str, WEIGHTS_VALUES)) + '}'
