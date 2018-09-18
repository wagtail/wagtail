from __future__ import absolute_import, unicode_literals


#
# Base classes
#


class SearchQuery:
    def __and__(self, other):
        return And([self, other])

    def __or__(self, other):
        return Or([self, other])

    def __invert__(self):
        return Not(self)


#
# Basic query classes
#


class PlainText(SearchQuery):
    OPERATORS = ['and', 'or']
    DEFAULT_OPERATOR = 'and'

    def __init__(self, query_string: str, operator: str = DEFAULT_OPERATOR,
                 boost: float = 1):
        self.query_string = query_string
        self.operator = operator.lower()
        if self.operator not in self.OPERATORS:
            raise ValueError("`operator` must be either 'or' or 'and'.")
        self.boost = boost


class MatchAll(SearchQuery):
    pass


class Boost(SearchQuery):
    def __init__(self, subquery: SearchQuery, boost: float):
        self.subquery = subquery
        self.boost = boost


#
# Combinators
#


class And(SearchQuery):
    def __init__(self, subqueries):
        self.subqueries = subqueries


class Or(SearchQuery):
    def __init__(self, subqueries):
        self.subqueries = subqueries


class Not(SearchQuery):
    def __init__(self, subquery: SearchQuery):
        self.subquery = subquery


MATCH_ALL = MatchAll()
