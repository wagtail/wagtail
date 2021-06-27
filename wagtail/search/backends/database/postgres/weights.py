from itertools import zip_longest

from django.apps import apps

from wagtail.search.index import Indexed
from wagtail.search.utils import get_search_fields


# This file contains the implementation of weights for PostgreSQL tsvectors. Only PostgreSQL has support for them, so that's why we define them here.


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
