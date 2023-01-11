import operator
import re
from functools import partial

from django.apps import apps
from django.db import connections

from wagtail.search.index import RelatedFields, SearchField

from .query import MATCH_NONE, Phrase, PlainText

NOT_SET = object()


def balanced_reduce(operator, seq, initializer=NOT_SET):
    """
    Has the same result as Python's reduce function, but performs the calculations in a different order.

    This is important when the operator is constructing data structures such as search query classes.
    This method will make the resulting data structures flatter, so operations that need to traverse
    them don't end up crashing with recursion errors.

    For example:

    Python's builtin reduce() function will do the following calculation:

    reduce(add, [1, 2, 3, 4, 5, 6, 7, 8])
    (1 + (2 + (3 + (4 + (5 + (6 + (7 + 8)))))))

    When using this with query classes, it would create a large data structure with a depth of 7
    Whereas balanced_reduce will execute this like so:

    balanced_reduce(add, [1, 2, 3, 4, 5, 6, 7, 8])
    ((1 + 2) + (3 + 4)) + ((5 + 6) + (7 + 8))

    Which only has a depth of 2
    """
    # Casting all iterables to list makes the implementation simpler
    if not isinstance(seq, list):
        seq = list(seq)

    # Note, it needs to be possible to use None as an initial value
    if initializer is not NOT_SET:
        if len(seq) == 0:
            return initializer
        else:
            return operator(initializer, balanced_reduce(operator, seq))

    if len(seq) == 0:
        raise TypeError("reduce() of empty sequence with no initial value")
    elif len(seq) == 1:
        return seq[0]
    else:
        break_point = len(seq) // 2
        first_set = balanced_reduce(operator, seq[:break_point])
        second_set = balanced_reduce(operator, seq[break_point:])
        return operator(first_set, second_set)


# Reduce any iterable to a single value using a logical OR e.g. (a | b | ...)
OR = partial(balanced_reduce, operator.or_)
# Reduce any iterable to a single value using a logical AND e.g. (a & b & ...)
AND = partial(balanced_reduce, operator.and_)
# Reduce any iterable to a single value using an addition
ADD = partial(balanced_reduce, operator.add)
# Reduce any iterable to a single value using a multiplication
MUL = partial(balanced_reduce, operator.mul)

MAX_QUERY_STRING_LENGTH = 255


def normalise_query_string(query_string):
    # Truncate query string
    query_string = query_string[:MAX_QUERY_STRING_LENGTH]
    # Convert query_string to lowercase
    query_string = query_string.lower()

    # Remove leading, trailing and multiple spaces
    query_string = re.sub(" +", " ", query_string).strip()

    return query_string


def separate_filters_from_query(query_string):
    filters_regexp = r'(\w+):(\w+|"[^"]+")'

    filters = {}
    for match_object in re.finditer(filters_regexp, query_string):
        key, value = match_object.groups()
        filters[key] = value.strip('"')

    query_string = re.sub(filters_regexp, "", query_string).strip()

    return filters, query_string


def parse_query_string(query_string, operator=None, zero_terms=MATCH_NONE):
    """
    This takes a query string typed in by a user and extracts the following:

     - Quoted terms (for phrase search)
     - Filters

    For example, the following query:

      `hello "this is a phrase" live:true` would be parsed into:

    filters: {'live': 'true'}
    tokens: And([PlainText('hello'), Phrase('this is a phrase')])
    """
    filters, query_string = separate_filters_from_query(query_string)

    is_phrase = False
    tokens = []
    for part in query_string.split('"'):
        part = part.strip()

        if part:
            if is_phrase:
                tokens.append(Phrase(part))
            else:
                tokens.append(
                    PlainText(part, operator=operator or PlainText.DEFAULT_OPERATOR)
                )

        is_phrase = not is_phrase

    if tokens:
        if operator == "or":
            search_query = OR(tokens)
        else:
            search_query = AND(tokens)
    else:
        search_query = zero_terms

    return filters, search_query


def get_descendant_models(model):
    """
    Returns all descendants of a model, including the model itself.
    """
    descendant_models = {
        other_model
        for other_model in apps.get_models()
        if issubclass(other_model, model)
    }
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

    return [
        ct.pk
        for ct in ContentType.objects.get_for_models(
            *model._meta.get_parent_list()
        ).values()
    ]


def get_descendants_content_types_pks(model):
    """
    Returns content types ids for the descendants of this model, including it.
    """
    from django.contrib.contenttypes.models import ContentType

    return [
        ct.pk
        for ct in ContentType.objects.get_for_models(
            *get_descendant_models(model)
        ).values()
    ]


def get_search_fields(search_fields):
    for search_field in search_fields:
        if isinstance(search_field, SearchField):
            yield search_field
        elif isinstance(search_field, RelatedFields):
            for sub_field in get_search_fields(search_field.fields):
                yield sub_field


def get_postgresql_connections():
    return [
        connection
        for connection in connections.all()
        if connection.vendor == "postgresql"
    ]
