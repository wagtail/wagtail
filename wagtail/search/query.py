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

    def __repr__(self):
        raise NotImplementedError


#
# Basic query classes
#


class PlainText(SearchQuery):
    OPERATORS = ["and", "or"]
    DEFAULT_OPERATOR = "and"

    def __init__(
        self, query_string: str, operator: str = DEFAULT_OPERATOR, boost: float = 1
    ):
        self.query_string = query_string
        self.operator = operator.lower()
        if self.operator not in self.OPERATORS:
            raise ValueError("`operator` must be either 'or' or 'and'.")
        self.boost = boost

    def __repr__(self):
        return "<PlainText {} operator={} boost={}>".format(
            repr(self.query_string), repr(self.operator), repr(self.boost)
        )


class Phrase(SearchQuery):
    def __init__(self, query_string: str):
        self.query_string = query_string

    def __repr__(self):
        return f"<Phrase {repr(self.query_string)}>"


class Fuzzy(SearchQuery):
    OPERATORS = ["and", "or"]
    DEFAULT_OPERATOR = "or"

    def __init__(self, query_string: str, operator: str = DEFAULT_OPERATOR):
        self.query_string = query_string
        self.operator = operator.lower()
        if self.operator not in self.OPERATORS:
            raise ValueError("`operator` must be either 'or' or 'and'.")

    def __repr__(self):
        return f"<Fuzzy {repr(self.query_string)} operator={repr(self.operator)}>"


class MatchAll(SearchQuery):
    def __repr__(self):
        return "<MatchAll>"


class Boost(SearchQuery):
    def __init__(self, subquery: SearchQuery, boost: float):
        self.subquery = subquery
        self.boost = boost

    def __repr__(self):
        return f"<Boost {repr(self.subquery)} boost={repr(self.boost)}>"


#
# Combinators
#


class And(SearchQuery):
    def __init__(self, subqueries):
        self.subqueries = subqueries

    def __repr__(self):
        return "<And {}>".format(
            " ".join(repr(subquery) for subquery in self.subqueries)
        )


class Or(SearchQuery):
    def __init__(self, subqueries):
        self.subqueries = subqueries

    def __repr__(self):
        return "<Or {}>".format(
            " ".join(repr(subquery) for subquery in self.subqueries)
        )


class Not(SearchQuery):
    def __init__(self, subquery: SearchQuery):
        self.subquery = subquery

    def __repr__(self):
        return f"<Not {repr(self.subquery)}>"


MATCH_ALL = MatchAll()
MATCH_NONE = Not(MATCH_ALL)
