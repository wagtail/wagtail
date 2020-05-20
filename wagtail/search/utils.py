import operator
import re
from functools import partial, reduce

from .query import MATCH_NONE, Phrase, PlainText

# Reduce any iterable to a single value using a logical OR e.g. (a | b | ...)
OR = partial(reduce, operator.or_)
# Reduce any iterable to a single value using a logical AND e.g. (a & b & ...)
AND = partial(reduce, operator.and_)
# Reduce any iterable to a single value using an addition
ADD = partial(reduce, operator.add)
# Reduce any iterable to a single value using a multiplication
MUL = partial(reduce, operator.mul)

MAX_QUERY_STRING_LENGTH = 255


def normalise_query_string(query_string):
    # Truncate query string
    if len(query_string) > MAX_QUERY_STRING_LENGTH:
        query_string = query_string[:MAX_QUERY_STRING_LENGTH]
    # Convert query_string to lowercase
    query_string = query_string.lower()

    # Remove leading, trailing and multiple spaces
    query_string = re.sub(' +', ' ', query_string).strip()

    return query_string


def separate_filters_from_query(query_string):
    filters_regexp = r'(\w+):(\w+|".+")'

    filters = {}
    for match_object in re.finditer(filters_regexp, query_string):
        key, value = match_object.groups()
        filters[key] = value.strip("\"")

    query_string = re.sub(filters_regexp, '', query_string).strip()

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
                tokens.append(PlainText(part, operator=operator or PlainText.DEFAULT_OPERATOR))

        is_phrase = not is_phrase

    if tokens:
        if operator == 'or':
            search_query = OR(tokens)
        else:
            search_query = AND(tokens)
    else:
        search_query = zero_terms

    return filters, search_query
