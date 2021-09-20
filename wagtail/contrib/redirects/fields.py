from django.db.models import CharField
from django.db.models.lookups import BuiltinLookup


class PatternField(CharField):
    """
    A subclass of `CharField` to have `PatternLookup` registered without
    polluting the global `CharField`.

    """
    pass


class PatternLookup(BuiltinLookup):
    """
    A lookup with the ability to match a given string with patterns stored in the row.

    Ends up with `WHERE "term" LIKE column`, where column may be `"%er%"`.
    """
    def as_sql(self, compiler, connection):
        lhs_sql, lhs_params = self.process_lhs(compiler, connection)
        rhs_sql, params = self.process_rhs(compiler, connection)

        # Swap the left and right
        lhs_sql, rhs_sql = rhs_sql, lhs_sql
        params.extend(lhs_params)

        rhs_sql = self.get_rhs_op(connection, rhs_sql)
        return '%s %s' % (lhs_sql, rhs_sql), params

    def get_rhs_op(self, connection, rhs):
        """
        It's basically an icontains lookup
        """
        return connection.operators["icontains"] % rhs


# Register as `__matches`
PatternField.register_lookup(PatternLookup, "matches")
