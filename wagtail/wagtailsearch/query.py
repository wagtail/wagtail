class SearchQuery:
    def __and__(self, other):
        return And([self, other])

    def __or__(self, other):
        return Or([self, other])

    def __invert__(self):
        return Not(self)


class SearchQueryOperator(SearchQuery):
    pass


class And(SearchQueryOperator):
    def __init__(self, subqueries):
        self.subqueries = subqueries


class Or(SearchQueryOperator):
    def __init__(self, subqueries):
        self.subqueries = subqueries


class Not(SearchQueryOperator):
    def __init__(self, subquery):
        self.subquery = subquery


class MatchAll(SearchQuery):
    pass


class PlainText(SearchQuery):
    def __init__(self, query_string, operator=None, boost=1.0):
        self.query_string = query_string
        self.operator = operator
        self.boost = boost


class Term(SearchQuery):
    def __init__(self, term, boost=1.0):
        self.term = term
        self.boost = boost


class Prefix(SearchQuery):
    def __init__(self, prefix, boost=1.0):
        self.prefix = prefix
        self.boost = boost


class Fuzzy(SearchQuery):
    def __init__(self, term, max_distance=3, boost=1.0):
        self.term = term
        self.max_distance = max_distance
        self.boost = boost


class Boost(SearchQuery):
    def __init__(self, query, boost):
        self.query = query
        self.boost = boost


class Filter(SearchQuery):
    def __init__(self, query, include=None, exclude=None):
        self.query = query
        self.include = include
        self.exclude = exclude


MATCH_ALL = MatchAll()
