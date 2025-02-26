import re
from typing import Any, Union

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.models.expressions import CombinedExpression, Expression, Value
from django.db.models.fields import BooleanField, Field
from django.db.models.sql.compiler import SQLCompiler


class LexemeCombinable(Expression):
    BITAND = "+"
    BITOR = ""
    invert = False  # By default, it is not inverted

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

    def __init__(
        self, value, output_field=None, invert=False, prefix=False, weight=None
    ):
        self.prefix = prefix
        self.invert = invert
        self.weight = weight

        if not value:
            raise ValueError("Lexeme value cannot be empty.")
        if re.search(r"\W+", value):
            raise ValueError(
                f"Lexeme value '{value}' must consist of alphanumeric characters and '_' only."
            )
        super().__init__(value, output_field=output_field)

    def as_sql(self, compiler, connection):
        param = self.value
        template = "%s"

        if self.prefix:
            param = f"{param}*"
        if self.invert:
            param = f"(-{param})"
        else:
            param = f"{param}"

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

        lhs_connector = self.connector
        rhs_connector = self.connector

        if (
            self.lhs.invert and self.connector == "+"
        ):  # NOTE: This is a special case for MySQL. If either side's operator is AND (+), and it is inverted, the operator should become NOT (-). If we did nothing, the result could would be '+X +(-Y)' for And(X, Not(Y)), which seems correct, but produces a wrong result. The solution is to turn the query into '+X -Y', which does work, and therefore this is done here.
            # TODO: There may be a better solution than this.
            modified_value = self.lhs.value.copy()
            modified_value.invert = not modified_value.invert
            lhs_connector = "-"
            lsql, params = compiler.compile(modified_value)
        else:
            lsql, params = compiler.compile(self.lhs)
        value_params.extend(params)

        if self.rhs.invert and self.connector == "+":  # Same explanation as above.
            modified_value = self.rhs.value.copy()
            modified_value.invert = not modified_value.invert
            rhs_connector = "-"
            rsql, params = compiler.compile(modified_value)
        else:
            rsql, params = compiler.compile(self.rhs)
        value_params.extend(params)

        combined_sql = "({}{} {}{})".format(
            lhs_connector, lsql, rhs_connector, rsql
        )  # if self.connector is '+' (AND), then both terms will be ANDed together. We need to repeat the connector to make that work.
        combined_value = combined_sql % tuple(value_params)
        return "%s", [combined_value]


class SearchQueryCombinable:
    BITAND = "+"
    BITOR = ""

    def _combine(self, other, connector: str, reversed: bool = False):
        if not isinstance(other, SearchQueryCombinable):
            raise TypeError(
                "SearchQuery can only be combined with other SearchQuery "
                "instances, got %s." % type(other).__name__
            )
        if reversed:
            return CombinedSearchQuery(other, connector, self)
        return CombinedSearchQuery(self, connector, other)

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


class SearchQuery(SearchQueryCombinable, Expression):
    def __init__(
        self, value: Union[LexemeCombinable, str], search_type: str = "lexeme", **extra
    ):
        super().__init__(output_field=SearchQueryField())
        self.extra = extra
        if (
            isinstance(value, str) or search_type == "phrase"
        ):  # If the value is a string, we assume it's a phrase
            safe_string = re.sub(
                r"\W+", " ", value
            )  # Remove non-word characters. This is done to disallow the usage of full text search operators in the MATCH clause, because MySQL doesn't include these kinds of characters in FULLTEXT indexes.
            self.value = Value(
                '"%s"' % safe_string
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


class CombinedSearchQuery(SearchQueryCombinable, CombinedExpression):
    def __init__(self, lhs, connector, rhs, output_field=None):
        super().__init__(lhs, connector, rhs, output_field)

    def __str__(self):
        return "%s" % super().__str__()

    def as_sql(self, compiler, connection):
        value_params = []

        lhs_connector = self.connector
        rhs_connector = self.connector

        if (
            isinstance(self.lhs, SearchQuery)
            and isinstance(self.lhs.value, Lexeme)
            and self.lhs.value.invert
            and self.connector == "+"
        ):  # NOTE: The explanation for this special case is the same as above, in the CombinedLexeme class.
            modified_value = self.lhs.value.copy()
            modified_value.invert = not modified_value.invert
            lhs_connector = "-"
            lsql, params = compiler.compile(modified_value)
        else:
            lsql, params = compiler.compile(self.lhs)
        value_params.extend(params)

        if (
            isinstance(self.rhs, SearchQuery)
            and isinstance(self.rhs.value, Lexeme)
            and self.rhs.value.invert
            and self.connector == "+"
        ):  # NOTE: The explanation for this special case is the same as above, in the CombinedLexeme class.
            modified_value = self.rhs.value.copy()
            modified_value.invert = not modified_value.invert
            rhs_connector = "-"
            rsql, params = compiler.compile(modified_value)
        else:
            rsql, params = compiler.compile(self.rhs)
        value_params.extend(params)

        combined_sql = "({}{} {}{})".format(
            lhs_connector, lsql, rhs_connector, rsql
        )  # if self.connector is '+' (AND), then both terms will be ANDed together. We need to repeat the connector to make that work.
        combined_value = combined_sql % tuple(value_params)
        return "%s", [combined_value]


class MatchExpression(Expression):
    filterable = True
    template = "MATCH (%s) AGAINST (%s IN BOOLEAN MODE)"

    def __init__(
        self,
        query: SearchQueryCombinable,
        columns: list[str] = None,
        output_field: Field = BooleanField(),
    ) -> None:
        super().__init__(output_field=output_field)
        self.query = query
        self.columns = (
            columns
            or [
                "title",
                "body",
            ]
        )  # We need to provide a default list of columns if the user doesn't specify one. We have a joint index for for 'title' and 'body' (see wagtail.search.migrations.0006_customise_indexentry), so we'll pick that one.

    def as_sql(self, compiler, connection):
        compiled_query = compiler.compile(self.query)  # Compile the query to a string
        formatted_query = compiled_query[0] % tuple(
            compiled_query[1]
        )  # Substitute the params in the query
        column_list = ", ".join(
            [f"`{column}`" for column in self.columns]
        )  # ['title', 'body'] becomes '`title`, `body`'
        params = [formatted_query]
        return (self.template % (column_list, "%s"), params)
