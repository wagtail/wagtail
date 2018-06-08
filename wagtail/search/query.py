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

    def apply(self, func):
        raise NotImplementedError

    def clone(self):
        return self.apply(lambda o: o)

    def get_children(self):
        return ()

    @property
    def children(self):
        return list(self.get_children())

    @property
    def child(self):
        children = self.children
        if len(children) != 1:
            raise IndexError('`%s` object has %d children, not a single child.'
                             % self.__class__.__name__, len(children))
        return children[0]


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

    def apply(self, func):
        return func(self.__class__(self.query_string, self.operator,
                                   self.boost))


class MatchAll(SearchQuery):
    def apply(self, func):
        return self.__class__()


class Boost(SearchQuery):
    def __init__(self, subquery: SearchQuery, boost: float):
        self.subquery = subquery
        self.boost = boost

    def apply(self, func):
        return func(self.__class__(self.subquery.apply(func), self.boost))


#
# Operators
#


class SearchQueryOperator(SearchQuery):
    pass


class MultiOperandsSearchQueryOperator(SearchQueryOperator):
    def __init__(self, subqueries):
        self.subqueries = subqueries

    def apply(self, func):
        return func(self.__class__(
            [subquery.apply(func) for subquery in self.subqueries]))

    def get_children(self):
        yield from self.subqueries


class And(MultiOperandsSearchQueryOperator):
    pass


class Or(MultiOperandsSearchQueryOperator):
    pass


class Not(SearchQueryOperator):
    def __init__(self, subquery: SearchQuery):
        self.subquery = subquery

    def apply(self, func):
        return func(self.__class__(self.subquery.apply(func)))

    def get_children(self):
        yield self.subquery


MATCH_ALL = MatchAll()
