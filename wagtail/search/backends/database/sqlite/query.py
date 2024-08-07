from typing import Any

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.models.expressions import CombinedExpression, Expression, Func, Value
from django.db.models.fields import BooleanField, Field, FloatField
from django.db.models.sql.compiler import SQLCompiler

from wagtail.search.query import And, MatchAll, Not, Or, Phrase, PlainText, SearchQuery


class BM25(Func):
    function = "bm25"
    output_field = FloatField()

    def __init__(self):
        expressions = ()
        super().__init__(*expressions)

    def as_sql(
        self,
        compiler: SQLCompiler,
        connection: BaseDatabaseWrapper,
        function=None,
        template=None,
    ):
        sql, params = "bm25(wagtailsearch_indexentry_fts)", []
        return sql, params


class LexemeCombinable(Expression):
    BITAND = "AND"
    BITOR = "OR"

    def _combine(self, other, connector, reversed, node=None):
        if not isinstance(other, LexemeCombinable):
            raise TypeError(
                f"Lexeme can only be combined with other Lexemes, got {type(other)}."
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


class SearchQueryField(Field):
    def db_type(self, connection):
        return None


class Lexeme(LexemeCombinable, Value):
    _output_field = SearchQueryField()

    def __init__(self, value, output_field=None, *, prefix=False, weight=None):
        self.prefix = prefix
        self.weight = weight
        super().__init__(value, output_field=output_field)

    def as_sql(self, compiler, connection):
        param = self.value.replace("'", "''").replace("\\", "\\\\")

        if self.prefix:
            template = '"%s"*'
        else:
            template = '"%s"'

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

        combined_sql = f"{lsql} {self.connector} {rsql}"
        combined_value = combined_sql % tuple(value_params)
        return "%s", [combined_value]


class SearchQueryCombinable:
    BITAND = "AND"
    BITOR = "OR"

    def _combine(self, other, connector: str, reversed: bool = False):
        if not isinstance(other, SearchQueryCombinable):
            raise TypeError(
                "SearchQuery can only be combined with other SearchQuery "
                "instances, got %s." % type(other).__name__
            )
        if reversed:
            return CombinedSearchQueryExpression(other, connector, self)
        return CombinedSearchQueryExpression(self, connector, other)

    # On Combinable, these are not implemented to reduce confusion with Q. In
    # this case we are actually (ab)using them to do logical combination so
    # it's consistent with other usage in Django.
    def __or__(self, other):
        return self._combine(other, self.BITOR, False)

    def __ror__(self, other):
        return self._combine(other, self.BITOR, True)

    def __and__(self, other):
        return self._combine(other, self.BITAND, False)

    def __rand__(self, other):
        return self._combine(other, self.BITAND, True)


class SearchQueryExpression(SearchQueryCombinable, Expression):
    def __init__(self, value: LexemeCombinable, using=None, **extra):
        super().__init__(output_field=SearchQueryField())
        self.using = using
        self.extra = extra
        if isinstance(value, str):  # If the value is a string, we assume it's a phrase
            self.value = Value(
                '"%s"' % value
            )  # We wrap it in quotes to make sure it's parsed as a phrase
        else:  # Otherwise, we assume it's a lexeme
            self.value = value

    def as_sql(
        self,
        compiler: SQLCompiler,
        connection: BaseDatabaseWrapper,
        **extra_context: Any,
    ) -> tuple[str, list[Any]]:
        sql, params = compiler.compile(self.value)
        return (sql, params)

    def __repr__(self) -> str:
        return self.value.__repr__()


class CombinedSearchQueryExpression(SearchQueryCombinable, CombinedExpression):
    def __init__(self, lhs, connector, rhs, output_field=None):
        super().__init__(lhs, connector, rhs, output_field)

    def __str__(self):
        return "(%s)" % super().__str__()


class MatchExpression(Expression):
    filterable = True
    template = (
        "wagtailsearch_indexentry_fts MATCH %s"  # TODO: Can the table name be inferred?
    )
    output_field = BooleanField()

    def __init__(self, columns: list[str], query: SearchQueryCombinable) -> None:
        super().__init__(output_field=self.output_field)
        self.columns = columns
        self.query = query

    def as_sql(self, compiler, connection):
        joined_columns = " ".join(
            self.columns
        )  # The format of the columns is 'column1 column2'
        compiled_query = compiler.compile(self.query)  # Compile the query to a string
        formatted_query = compiled_query[0] % tuple(
            compiled_query[1]
        )  # Substitute the params in the query
        params = [
            "{{{column}}} : ({query})".format(
                column=joined_columns, query=formatted_query
            )
        ]  # Build the full MATCH search query. It will be a parameter to the template, so no SQL injections are possible here.
        return (self.template, params)

    def __repr__(self):
        return f"<MatchExpression: {self.columns!r} = {self.query!r}>"


class AndNot(SearchQuery):
    """
    This is a binary search query, where there are two subqueries, and the search is done by searching the first, and excluding the second subquery.
    For example, AndNot(X, Y) would be equivalent to doing And(X, Not(Y)), where X is the first subquery, and Y is the second subquery (the negated one).
    This is done because the SQLite FTS5 module doesn't support the unary NOT operator.
    """

    def __init__(self, subquery_a: SearchQuery, subquery_b: SearchQuery):
        self.subquery_a = subquery_a
        self.subquery_b = subquery_b

    def __repr__(self):
        return f"<{repr(self.subquery_a)} AndNot {repr(self.subquery_b)}>"


def normalize(search_query: SearchQuery) -> tuple[SearchQuery]:
    """
    Turns this query into a normalized version.
    For example, And(Not(PlainText("Arepa")), PlainText("Crepe")) would be turned into AndNot(PlainText("Crepe"), PlainText("Arepa")): "Crepe AND NOT Arepa".
    This is done because we need to get the NOT operator to the front of the query, so it can be used in the search, because the SQLite FTS5 module doesn't support the unary NOT operator. This means that, in order to support the NOT operator, we need to match against the non-negated version of the query, and then return everything that is not in the results of the non-negated query.
    """
    if isinstance(search_query, Phrase):
        return search_query  # We can't normalize a Phrase.
    if isinstance(search_query, PlainText):
        return search_query  # We can't normalize a PlainText.
    if isinstance(search_query, And):
        normalized_subqueries: list[SearchQuery] = [
            normalize(subquery) for subquery in search_query.subqueries
        ]  # This builds a list of normalized subqueries.

        not_negated_subqueries = [
            subquery
            for subquery in normalized_subqueries
            if not isinstance(subquery, Not)
        ]  # All the non-negated subqueries.
        not_negated_subqueries = [
            subquery
            for subquery in not_negated_subqueries
            if not isinstance(subquery, MatchAll)
        ]  # We can ignore all MatchAll SearchQueries here, because they are redundant.
        negated_subqueries = [
            subquery.subquery
            for subquery in normalized_subqueries
            if isinstance(subquery, Not)
        ]

        if (
            negated_subqueries == []
        ):  # If there are no negated subqueries, return an And(), now without the redundant MatchAll subqueries.
            return And(not_negated_subqueries)

        for subquery in (
            negated_subqueries
        ):  # If there's a negated MatchAll subquery, then nothing will get matched.
            if isinstance(subquery, MatchAll):
                return Not(MatchAll())

        return AndNot(And(not_negated_subqueries), Or(negated_subqueries))
    if isinstance(search_query, Or):
        normalized_subqueries: list[SearchQuery] = [
            normalize(subquery) for subquery in search_query.subqueries
        ]  # This builds a list of (subquery, negated) tuples.

        negated_subqueries = [
            subquery.subquery
            for subquery in normalized_subqueries
            if isinstance(subquery, Not)
        ]
        if (
            negated_subqueries == []
        ):  # If there are no negated subqueries, return an Or().
            return Or(normalized_subqueries)

        for subquery in (
            negated_subqueries
        ):  # If there's a MatchAll subquery, then anything will get matched.
            if isinstance(subquery, MatchAll):
                return MatchAll()

        not_negated_subqueries = [
            subquery
            for subquery in normalized_subqueries
            if not isinstance(subquery, Not)
        ]  # All the non-negated subqueries.
        not_negated_subqueries = [
            subquery
            for subquery in not_negated_subqueries
            if not isinstance(subquery, MatchAll)
        ]  # We can ignore all MatchAll SearchQueries here, because they are redundant.

        return AndNot(MatchAll(), And(negated_subqueries))
    if isinstance(search_query, Not):
        normalized = normalize(search_query.subquery)
        return Not(normalized)  # Normalize the subquery, then invert it.
    if isinstance(search_query, MatchAll):
        return search_query  # We can't normalize a MatchAll.
