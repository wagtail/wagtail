from __future__ import absolute_import, unicode_literals

from django.contrib.postgres.search import SearchQueryCombinable, SearchQueryField
from django.db.models.expressions import Expression, Value


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
    OPERATORS = ['and', 'or']
    DEFAULT_OPERATOR = 'and'

    def __init__(self, query_string: str, operator: str = DEFAULT_OPERATOR,
                 boost: float = 1):
        self.query_string = query_string
        self.operator = operator.lower()
        if self.operator not in self.OPERATORS:
            raise ValueError("`operator` must be either 'or' or 'and'.")
        self.boost = boost

    def __repr__(self):
        return '<PlainText {} operator={} boost={}>'.format(repr(self.query_string), repr(self.operator), repr(self.boost))


class Phrase(SearchQuery):
    def __init__(self, query_string: str):
        self.query_string = query_string

    def __repr__(self):
        return '<Phrase {}>'.format(repr(self.query_string))


class MatchAll(SearchQuery):
    def __repr__(self):
        return '<MatchAll>'


class Boost(SearchQuery):
    def __init__(self, subquery: SearchQuery, boost: float):
        self.subquery = subquery
        self.boost = boost

    def __repr__(self):
        return '<Boost {} boost={}>'.format(repr(self.subquery), repr(self.boost))


#
# Combinators
#


class And(SearchQuery):
    def __init__(self, subqueries):
        self.subqueries = subqueries

    def __repr__(self):
        return '<And {}>'.format(' '.join(repr(subquery) for subquery in self.subqueries))


class Or(SearchQuery):
    def __init__(self, subqueries):
        self.subqueries = subqueries

    def __repr__(self):
        return '<Or {}>'.format(' '.join(repr(subquery) for subquery in self.subqueries))


class Not(SearchQuery):
    def __init__(self, subquery: SearchQuery):
        self.subquery = subquery

    def __repr__(self):
        return '<Not {}>'.format(repr(self.subquery))


MATCH_ALL = MatchAll()
MATCH_NONE = Not(MATCH_ALL)


class LexemeCombinable(Expression):
    BITAND = '&'
    BITOR = '|'

    def _combine(self, other, connector, reversed, node=None):
        if not isinstance(other, LexemeCombinable):
            raise TypeError(
                'Lexeme can only be combined with other Lexemes, '
                'got {}.'.format(type(other))
            )
        if reversed:
            return CombinedLexeme(other, connector, self)
        return CombinedLexeme(self, connector, other)

    # On Combinable, these are not implemented to reduce confusion with Q. In
    # this case we are actually (ab)using them to do logical combination so
    # it's consistent with other usage in Django.
    def bitand(self, other):
        return self._combine(other, self.BITAND, False)

    def bitor(self, other):
        return self._combine(other, self.BITOR, False)

    def __or__(self, other):
        return self._combine(other, self.BITOR, False)

    def __and__(self, other):
        return self._combine(other, self.BITAND, False)


class Lexeme(LexemeCombinable, Value):
    _output_field = SearchQueryField()

    def __init__(self, value, output_field=None, *, invert=False, prefix=False, weight=None):
        self.prefix = prefix
        self.invert = invert
        self.weight = weight
        super().__init__(value, output_field=output_field)

    def as_sql(self, compiler, connection):
        param = "'%s'" % self.value.replace("'", "''").replace("\\", "\\\\")

        template = "%s"

        label = ''
        if self.prefix:
            label += '*'
        if self.weight:
            label += self.weight

        if label:
            param = '{}:{}'.format(param, label)
        if self.invert:
            param = '!{}'.format(param)

        return template, [param]


class CombinedLexeme(LexemeCombinable):
    _output_field = SearchQueryField()

    def __init__(self, lhs, connector, rhs, output_field=None):
        super().__init__(output_field=output_field)
        self.connector = connector
        self.lhs = lhs
        self.rhs = rhs

    def as_sql(self, compiler, connection):
        value_params = []
        lsql, params = compiler.compile(self.lhs)
        value_params.extend(params)

        rsql, params = compiler.compile(self.rhs)
        value_params.extend(params)

        combined_sql = '({} {} {})'.format(lsql, self.connector, rsql)
        combined_value = combined_sql % tuple(value_params)
        return '%s', [combined_value]


# This class is required for Django 3.0 support and below
# In Django 3.1 onwards, we can replace this with SearchQuery(expression, search_type='raw')
# The PR for the functionality we need is here: https://github.com/django/django/pull/12525
class RawSearchQuery(SearchQueryCombinable, Expression):
    _output_field = SearchQueryField()

    def __init__(self, expressions, output_field=None, *, config=None, invert=False):
        self.config = config
        self.invert = invert
        self.expressions = expressions
        super().__init__(output_field=output_field)

    def resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False):
        resolved = super().resolve_expression(query, allow_joins, reuse, summarize, for_save)
        if self.config:
            if not hasattr(self.config, 'resolve_expression'):
                resolved.config = Value(self.config).resolve_expression(query, allow_joins, reuse, summarize, for_save)
            else:
                resolved.config = self.config.resolve_expression(query, allow_joins, reuse, summarize, for_save)
        return resolved

    def as_sql(self, compiler, connection):
        sql, params, = compiler.compile(self.expressions)

        if self.config:
            config_sql, config_params = compiler.compile(self.config)
            template = 'to_tsquery({}::regconfig, {})'.format(config_sql, sql)
            params = config_params + params
        else:
            template = 'to_tsquery({})'.format(sql)
        if self.invert:
            template = '!!({})'.format(template)
        return template, params

    def _combine(self, *args, **kwargs):
        combined = super()._combine(*args, **kwargs)
        combined.output_field = SearchQueryField()
        return combined

    def __invert__(self):
        return type(self)(self.lexeme, config=self.config, invert=not self.invert)
