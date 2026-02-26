import re

from modelsearch.query import MATCH_NONE, Phrase, PlainText
from modelsearch.utils import *  # noqa: F403
from modelsearch.utils import AND, OR, separate_filters_from_query


def parse_query_string(query_string, operator=None, zero_terms=MATCH_NONE):
    filters, query_string = separate_filters_from_query(query_string)

    is_phrase = False
    tokens = []

    if '"' in query_string:
        parts = query_string.split('"')
    elif re.search(r"(?<!\w)'|'(?!\w)", query_string):
        # Only split on apostrophes that are NOT inside a word
        # e.g. 'hot cross bun' → phrase, but it's → plain text
        parts = re.split(r"(?<!\w)'|'(?!\w)", query_string)
    else:
        parts = [query_string]

    for part in parts:
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
