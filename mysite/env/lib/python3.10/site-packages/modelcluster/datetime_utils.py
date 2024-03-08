import datetime

from django import forms


TIMEFIELD_TRANSFORM_EXPRESSIONS = {"hour", "minute", "second"}
DATEFIELD_TRANSFORM_EXPRESSIONS = {
    "year",
    "iso_year",
    "month",
    "day",
    "week",
    "week_day",
    "iso_week_day",
    "quarter",
}
DATETIMEFIELD_TRANSFORM_EXPRESSIONS = (
    {"date", "time"}
    | TIMEFIELD_TRANSFORM_EXPRESSIONS
    | DATEFIELD_TRANSFORM_EXPRESSIONS
)
TRANSFORM_FIELD_TYPES = {
    "year": forms.IntegerField,
    "iso_year": forms.IntegerField,
    "month": forms.IntegerField,
    "hour": forms.IntegerField,
    "minute": forms.IntegerField,
    "second": forms.IntegerField,
    "day": forms.IntegerField,
    "week": forms.IntegerField,
    "week_day": forms.IntegerField,
    "iso_week_day": forms.IntegerField,
    "quarter": forms.IntegerField,
    "date": forms.DateField,
    "time": forms.TimeField,
}


def derive_from_value(value, expr):
    if isinstance(value, datetime.datetime):
        return derive_from_datetime(value, expr)
    if isinstance(value, datetime.date):
        return derive_from_date(value, expr)
    if isinstance(value, datetime.time):
        return derive_from_time(value, expr)
    return None


def derive_from_time(value, expr):
    """
    Mimics the behaviour of the ``hour``, ``minute`` and ``second`` lookup
    expressions that Django querysets support for ``TimeField`` and
    ``DateTimeField``, by extracting the relevant value from an in-memory
    ``time`` or ``datetime`` value.
    """
    if expr == "hour":
        return value.hour
    if expr == "minute":
        return value.minute
    if expr == "second":
        return value.second
    raise ValueError(
        "Expression '{expression}' is not supported for {value}".format(
            expression=expr, value=repr(value)
        )
    )


def derive_from_date(value, expr):
    """
    Mimics the behaviour of the ``year``, ``iso_year`` ``month``, ``day``,
    ``week``, ``week_day``, ``iso_week_day`` and ``quarter`` lookup
    expressions that Django querysets support for ``DateField`` and
    ``DateTimeField`` columns, by extracting the relevant value from an
    in-memory ``date`` or ``datetime`` value.
    """
    if expr == "year":
        return value.year
    if expr == "iso_year":
        return value.isocalendar()[0]
    if expr == "month":
        return value.month
    if expr == "day":
        return value.day
    if expr == "week":
        return value.isocalendar()[1]
    if expr == "week_day":
        v = value.isoweekday()
        return 1 if v == 7 else v + 1
    if expr == "iso_week_day":
        return value.isoweekday()
    if expr == "quarter":
        return (value.month - 1) // 3 + 1
    raise ValueError(
        "Expression '{expression}' is not supported for {value}".format(
            expression=expr, value=repr(value)
        )
    )


def derive_from_datetime(value, expr):
    """
    Mimics the behaviour of the ``date``, ``time`` and other lookup
    expressions that Django querysets support for ``DateTimeField`` columns,
    by extracting the relevant value from an in-memory ``datetime`` value.
    """
    if expr == "date":
        return value.date()
    if expr == "time":
        return value.time()
    if expr in TIMEFIELD_TRANSFORM_EXPRESSIONS:
        return derive_from_time(value, expr)
    if expr in DATEFIELD_TRANSFORM_EXPRESSIONS:
        return derive_from_date(value, expr)
    raise ValueError(
        "Expression '{expression}' is not supported for {value}".format(
            expression=expr, value=repr(value)
        )
    )
