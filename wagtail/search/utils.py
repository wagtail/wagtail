import operator
import re
import string
from functools import partial, reduce

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

    # Strip punctuation characters
    query_string = ''.join([c for c in query_string if c not in string.punctuation])

    # Remove double spaces
    query_string = ' '.join(query_string.split())

    return query_string


def separate_filters_from_query(query_string):
    filters_regexp = r'(\w+):(\w+|".+")'

    filters = {}
    for match_object in re.finditer(filters_regexp, query_string):
        key, value = match_object.groups()
        filters[key] = value.strip("\"")

    query_string = re.sub(filters_regexp, '', query_string).strip()

    return filters, query_string
