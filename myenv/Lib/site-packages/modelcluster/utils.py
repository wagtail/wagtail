import datetime
from functools import lru_cache
import random
from django.core.exceptions import FieldDoesNotExist
from django.db.models import (
    DateField,
    DateTimeField,
    ManyToManyField,
    ManyToManyRel,
    Model,
    TimeField,
)

from modelcluster import datetime_utils


REL_DELIMETER = "__"


class ManyToManyTraversalError(ValueError):
    pass


class NullRelationshipValueEncountered(Exception):
    pass


class TraversedRelationship:
    __slots__ = ['from_model', 'field']

    def __init__(self, from_model, field):
        self.from_model = from_model
        self.field = field

    @property
    def field_name(self) -> str:
        return self.field.name

    @property
    def to_model(self):
        return self.field.target_model


@lru_cache(maxsize=None)
def get_model_field(model, name):
    """
    Returns a model field matching the supplied ``name``, which can include
    double-underscores (`'__'`) to indicate relationship traversal - in which
    case, the model field will be lookuped up from the related model.

    Multiple traversals for the same field are supported, but at this
    moment in time, only traversal of many-to-one and one-to-one relationships
    is supported.

    Details of any relationships traversed in order to reach the returned
    field are made available as `field.traversals`. The value is a tuple of
    ``TraversedRelationship`` instances.

    Raises ``FieldDoesNotExist`` if the name cannot be mapped to a model field.
    """
    subject_model = model
    traversals = []
    field = None
    for field_name in name.split(REL_DELIMETER):

        if field is not None:
            if isinstance(field, (ManyToManyField, ManyToManyRel)):
                raise ManyToManyTraversalError(
                    "The lookup '{name}' from {model} cannot be replicated "
                    "by modelcluster, because the '{field_name}' "
                    "relationship from {subject_model} is a many-to-many, "
                    "and traversal is only supported for one-to-one or "
                    "many-to-one relationships."
                    .format(
                        name=name,
                        model=model,
                        field_name=field_name,
                        subject_model=subject_model,
                    )
                )
            elif getattr(field, "related_model", None):
                traversals.append(TraversedRelationship(subject_model, field))
                subject_model = field.related_model
            elif (
                (
                    isinstance(field, DateTimeField)
                    and field_name in datetime_utils.DATETIMEFIELD_TRANSFORM_EXPRESSIONS
                ) or (
                    isinstance(field, DateField)
                    and field_name in datetime_utils.DATEFIELD_TRANSFORM_EXPRESSIONS
                ) or (
                    isinstance(field, TimeField)
                    and field_name in datetime_utils.TIMEFIELD_TRANSFORM_EXPRESSIONS
                )
            ):
                transform_field_type = datetime_utils.TRANSFORM_FIELD_TYPES[field_name]
                field = transform_field_type()
                break
            else:
                raise FieldDoesNotExist(
                    "Failed attempting to traverse from {from_field} (a {from_field_type}) to '{to_field}'."
                    .format(
                        from_field=subject_model._meta.label + '.' + field.name,
                        from_field_type=type(field),
                        to_field=field_name,
                    )
                )
        try:
            field = subject_model._meta.get_field(field_name)
        except FieldDoesNotExist:
            if field_name.endswith("_id"):
                field = subject_model._meta.get_field(field_name[:-3]).target_field
            raise

    field.traversals = tuple(traversals)
    return field


def extract_field_value(obj, key, pk_only=False, suppress_fielddoesnotexist=False, suppress_nullrelationshipvalueencountered=False):
    """
    Attempts to extract a field value from ``obj`` matching the ``key`` - which,
    can contain double-underscores (`'__'`) to indicate traversal of relationships
    to related objects.

    For keys that specify ``ForeignKey`` or ``OneToOneField`` field values, full
    related objects are returned by default. If only the primary key values are
    required ((.g. when ordering, or using ``values()`` or ``values_list()``)),
    call the function with ``pk_only=True``.

    By default, ``FieldDoesNotExist`` is raised if the key cannot be mapped to
    a model field. Call the function with ``suppress_fielddoesnotexist=True``
    to instead receive a ``None`` value when this occurs.

    By default, ``NullRelationshipValueEncountered`` is raised if a ``None``
    value is encountered while attempting to traverse relationships in order to
    access further fields. Call the function with
    ``suppress_nullrelationshipvalueencountered`` to instead receive a ``None``
    value when this occurs.
    """
    source = obj
    latest_obj = obj
    segments = key.split(REL_DELIMETER)
    for i, segment in enumerate(segments, start=1):
        if (
            (
                isinstance(source, datetime.datetime)
                and segment in datetime_utils.DATETIMEFIELD_TRANSFORM_EXPRESSIONS
            )
            or (
                isinstance(source, datetime.date)
                and segment in datetime_utils.DATEFIELD_TRANSFORM_EXPRESSIONS
            )
            or (
                isinstance(source, datetime.time)
                and segment in datetime_utils.TIMEFIELD_TRANSFORM_EXPRESSIONS
            )
        ):
            source = datetime_utils.derive_from_value(source, segment)
            value = source
        elif hasattr(source, segment):
            value = getattr(source, segment)
            if isinstance(value, Model):
                latest_obj = value
            if value is None and i < len(segments):
                if suppress_nullrelationshipvalueencountered:
                    return None
                raise NullRelationshipValueEncountered(
                    "'{key}' cannot be reached for {obj} because {model_class}.{field_name} "
                    "is null.".format(
                        key=key,
                        obj=repr(obj),
                        model_class=latest_obj._meta.label,
                        field_name=segment,
                    )
                )
            source = value
        elif suppress_fielddoesnotexist:
            return None
        else:
            raise FieldDoesNotExist(
                "'{name}' is not a valid field name for {model}".format(
                    name=segment, model=type(source)
                )
            )
    if pk_only and hasattr(value, 'pk'):
        return value.pk
    return value


def sort_by_fields(items, fields):
    """
    Sort a list of objects on the given fields. The field list works analogously to
    queryset.order_by(*fields): each field is either a property of the object,
    or is prefixed by '-' (e.g. '-name') to indicate reverse ordering.
    """
    # To get the desired behaviour, we need to order by keys in reverse order
    # See: https://docs.python.org/2/howto/sorting.html#sort-stability-and-complex-sorts
    for key in reversed(fields):
        if key == '?':
            random.shuffle(items)
            continue

        # Check if this key has been reversed
        reverse = False
        if key[0] == '-':
            reverse = True
            key = key[1:]

        def get_sort_value(item):
            # Use a tuple of (v is not None, v) as the key, to ensure that None sorts before other values,
            # as comparing directly with None breaks on python3
            value = extract_field_value(item, key, pk_only=True, suppress_fielddoesnotexist=True, suppress_nullrelationshipvalueencountered=True)
            return (value is not None, value)

        # Sort items
        items.sort(key=get_sort_value, reverse=reverse)
