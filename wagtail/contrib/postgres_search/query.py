# Originally from https://github.com/django/django/pull/8313
# Resubmitted in https://github.com/django/django/pull/12727

# If that PR gets merged, we should be able to replace this with the version in Django.

from django.contrib.postgres.search import SearchQueryCombinable, SearchQueryField
from django.db.models.expressions import Expression, Value


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
