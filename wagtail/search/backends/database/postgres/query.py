from django.contrib.postgres.search import SearchQueryField
from django.db.models.expressions import Expression, Value


class LexemeCombinable(Expression):
    BITAND = "&"
    BITOR = "|"

    def _combine(self, other, connector, reversed, node=None):
        if not isinstance(other, LexemeCombinable):
            raise TypeError(
                "Lexeme can only be combined with other Lexemes, "
                "got {}.".format(type(other))
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

    def __init__(
        self, value, output_field=None, *, invert=False, prefix=False, weight=None
    ):
        self.prefix = prefix
        self.invert = invert
        self.weight = weight
        super().__init__(value, output_field=output_field)

    def as_sql(self, compiler, connection):
        param = "'%s'" % self.value.replace("'", "''").replace("\\", "\\\\")

        template = "%s"

        label = ""
        if self.prefix:
            label += "*"
        if self.weight:
            label += self.weight

        if label:
            param = "{}:{}".format(param, label)
        if self.invert:
            param = "!{}".format(param)

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

        combined_sql = "({} {} {})".format(lsql, self.connector, rsql)
        combined_value = combined_sql % tuple(value_params)
        return "%s", [combined_value]
