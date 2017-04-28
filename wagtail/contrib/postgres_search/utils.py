from __future__ import absolute_import, division, unicode_literals

import operator
import re
from functools import partial, reduce

from django.apps import apps
from django.db import connections
from django.db.models import Q
from django.utils.lru_cache import lru_cache
from django.utils.six.moves import zip_longest

from wagtail.wagtailsearch.index import Indexed, RelatedFields, SearchField

try:
    # Only use the GPLv2 licensed unidecode if it's installed.
    from unidecode import unidecode
except ImportError:
    def unidecode(value):
        return value


def get_postgresql_connections():
    return [connection for connection in connections.all()
            if connection.vendor == 'postgresql']


# Reduce any iterable to a single value using a logical OR e.g. (a | b | ...)
OR = partial(reduce, operator.or_)
# Reduce any iterable to a single value using a logical AND e.g. (a & b & ...)
AND = partial(reduce, operator.and_)
# Reduce any iterable to a single value using an addition
ADD = partial(reduce, operator.add)


def keyword_split(keywords):
    """
    Return all the keywords in a keyword string.

    Keeps keywords surrounded by quotes together, removing the surrounding quotes:

    >>> keyword_split('Hello I\\'m looking for "something special"')
    ['Hello', "I'm", 'looking', 'for', 'something special']

    Nested quoted strings are returned as is:

    >>> keyword_split("He said \\"I'm looking for 'something special'\\" so I've given him the 'special item'")
    ['He', 'said', "I'm looking for 'something special'", 'so', "I've", 'given', 'him', 'the', 'special item']

    """
    matches = re.findall(r'"([^"]+)"|\'([^\']+)\'|(\S+)', keywords)
    return [match[0] or match[1] or match[2] for match in matches]


def get_descendant_models(model):
    """
    Returns all descendants of a model, including the model itself.
    """
    descendant_models = {other_model for other_model in apps.get_models()
                         if issubclass(other_model, model)}
    descendant_models.add(model)
    return descendant_models


def get_descendants_content_types_pks(models, db_alias):
    return get_content_types_pks(
        tuple(descendant_model for model in models
              for descendant_model in get_descendant_models(model)), db_alias)


@lru_cache()
def get_content_types_pks(models, db_alias):
    # We import it locally because this file is loaded before apps are ready.
    from django.contrib.contenttypes.models import ContentType
    return list(ContentType._default_manager.using(db_alias)
                .filter(OR([Q(app_label=model._meta.app_label,
                              model=model._meta.model_name)
                            for model in models]))
                .values_list('pk', flat=True))


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


def get_weight(boost):
    if boost is None:
        return WEIGHTS[-1]
    for max_boost, weight in BOOSTS_WEIGHTS:
        if boost >= max_boost:
            return weight
    return weight
