from functools import lru_cache
from typing import Dict, List, Set, Tuple

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db.models import OneToOneRel, Q
from django.db.models.base import ModelBase


class NoConcreteSubclassesError(Exception):
    pass


class AbstractModelError(Exception):
    pass


class UnreachableSubclassError(Exception):
    pass


@lru_cache(maxsize=None)
def get_concrete_subclasses(model_class: ModelBase) -> Tuple[ModelBase]:
    """
    Returns a tuple of all known subclass of ``model_class`` that are
    concrete (have their own database table).
    """
    return tuple(
        model
        for model in apps.get_models()
        if not model._meta.abstract and issubclass(model, model_class)
    )


def get_concrete_subclasses_with_fields(
    model_class=ModelBase, *field_names: str
) -> Set[ModelBase]:
    """
    Returns a set of concrete ``model_class`` subclasses that have fields
    matching all the supplied ``field_names`` (including ``model_class``
    itself, where relevant).
    """
    all_subclasses = get_concrete_subclasses(model_class)
    relevant_subclasses = set(all_subclasses)

    for field_name in field_names:
        # No items should be removed, as all subclasses have this field
        if not has_field(model_class, field_name):
            try:
                # Remove items that do not have this field
                relevant_subclasses.intersection_update(
                    {s for s in all_subclasses if has_field(s, field_name)}
                )
                if not relevant_subclasses:
                    # If there are no relevant types left over, exit here
                    return relevant_subclasses
            except (FieldDoesNotExist, ValueError):
                # No models have this field
                return set()

    return relevant_subclasses


@lru_cache(maxsize=None)
def get_all_field_names(model_class: ModelBase) -> Tuple[str]:
    return tuple(
        f.name
        for f in model_class._meta.get_fields(include_parents=True, include_hidden=True)
    )


@lru_cache(maxsize=None)
def has_field(model_class: ModelBase, field_name: str) -> bool:
    """
    Returns a boolean indicating whether the supplied ``model_class``
    has a ``Field`` matching the provided ``field_name`` (whether
    inherited, automatically added by Django, or otherwise).
    """
    try:
        # NOTE: Will work for non-hidden fields
        model_class._meta.get_field(field_name)
        return True
    except FieldDoesNotExist:
        return field_name in get_all_field_names(model_class)


@lru_cache(maxsize=None)
def get_concrete_subclass_lookups(
    model_class: ModelBase, for_field: str = None
) -> Dict[ModelBase, str]:
    """
    Returns a dictionary of concrete ``model_class`` subclasses, along with
    string values that can be used to span the relevant one-to-one
    relationships to reach those models in Django ORM queries.

    If ``for_field`` is supplied, only concrete subclasses that
    implement that field will be included in the return value.

    Raises ``wagtail.core.mti_utils.AbstractModelError`` if the provided
    ``model_class`` is abstract.

    Raises ``wagtail.core.mti_utils.NoConcreteSubclassesError`` if the
    provided model has no concrete subclasses that can be accessed from
    ``model_class`` via the Django ORM.

    Raises ``django.core.exceptions.FieldDoesNotExist`` if ``for_field``
    is supplied, and no concrete subclasses with that field can be accessed
    from ``model_class`` via the Django ORM.
    """

    if model_class._meta.abstract:
        raise AbstractModelError(
            "Subclass lookups only work from concrete models, but the provided "
            f"model '{model_class._meta.label}' is abstract."
        )

    if for_field and has_field(model_class, for_field):
        return {}

    results = _get_concrete_subclass_lookups(model_class, for_field=for_field)

    if not results:
        if for_field:
            raise FieldDoesNotExist(
                f"The model class '{model_class._meta.label}' has no concrete subclasses with a field named '{for_field}' that are accessible via the Django ORM."
            )
        raise NoConcreteSubclassesError(
            f"The model class '{model_class._meta.label}' has no concrete subclasses that are accessible via the Django ORM."
        )
    return results


def _get_concrete_subclass_lookups(
    model_class: ModelBase,
    for_field: str = None,
    prefix: str = None,
    add_to: Dict[ModelBase, str] = None,
    known_subclasses: tuple = None,
) -> Dict[ModelBase, str]:
    """
    Used by get_concrete_subclass_lookups() to compile the return value.
    Calls itself recursively to span any number of one-to-one relationships.
    """
    return_value = {} if add_to is None else add_to

    if known_subclasses is None:
        known_subclasses = get_concrete_subclasses(model_class)

    for rel in (
        rel
        for rel in model_class._meta.related_objects
        if isinstance(rel, OneToOneRel) and rel.related_model in known_subclasses
    ):
        access_string = f"{prefix}__{rel.name}" if prefix else rel.name

        if for_field:
            if has_field(rel.related_model, for_field):
                return_value[rel.related_model] = access_string
            else:
                # only continue to search subclasses if the related model
                # didn't implement the field itself
                _get_concrete_subclass_lookups(
                    rel.related_model,
                    for_field=for_field,
                    prefix=access_string,
                    add_to=return_value,
                    known_subclasses=known_subclasses,
                )
        else:
            return_value[rel.related_model] = access_string
            _get_concrete_subclass_lookups(
                rel.related_model,
                add_to=return_value,
                known_subclasses=known_subclasses,
                for_field=for_field,
                prefix=access_string,
            )

    return return_value


def get_subclass_spanning_q_list(model, q_list, filter_kwargs) -> List[Q]:
    """
    Converts any ``Q`` objects and keyword arguments passed to
    ``PageQuerySet.specific_filter()``, ``PageQuerySet.specific_exclude()``
    or ``PageQuerySet.specific_get()`` to a list of ``Q`` objects that span
    relationships to reach fields on concrete subclasses.
    """
    return [get_subclass_spanning_q(model, q) for q in q_list] + [
        get_subclass_spanning_q(model, Q(**{key: value}))
        for key, value in sorted(filter_kwargs.items())
    ]


def get_subclass_spanning_q(model: ModelBase, original_q: Q) -> Q:
    """
    Receives a model class and a ``Q`` object, where field names in the
    ``Q``s filter strings may correspond to fields on ``model`` or one or
    more of its concrete subclasses, and returns a new ``Q`` with its
    ``children`` 'expanded' so that those filter strings span the correct
    tables to access fields on subclasses, and include matches from
    any of those subclasses.

    For example, say the following ``Q`` was provided:

    .. code-block:: python

        Q(
            live=True,
            popularity__gte=50,
            start_date__year__in=(2021, 2022),
        )

    If this were a query from Wagtail's ``Page`` model, ``live`` is a field on
    the ``Page`` class, so ``live=True`` will work as it is. but the other two
    fields (`popularity` and ``start_datetime``) are not. What the developer
    really means is: They want to filter the pages based on fields that
    they have added to custom Page types in their project.

    To access those fields, these filter strings need 'prepending' with the
    necessary 'modelname__' string to allow the fields to be accessed, and the
    simple single filter needs converting to a chain of **OR** joined
    ``Q`` queries, so that matches will be included for all versions of that
    field.

    Taking the ``popularity__gte=50`` filter as an example. If ``Page`` had
    five concrete subclasses, and three of those subclasses had the field
    ``popularity``. The replacement ``Q`` would look something like this:

    .. code-block:: python

        Q(
            Q(blogpage__popularity__gte=50) |
            Q(eventpage__popularity__gte=50) |
            Q(specialeventpage__popularity__gte=50) |
        )

    Taking the ``start_date__year__in=(2021, 2022)`` filter as another example.
    If ``Page`` had two subclasses with the field ``start_date``, the
    replacement ``Q`` would look something like this:

    .. code-block:: python

        Q(
            Q(eventpage__start_date__year__in=(2021, 2022)) |
            Q(specialeventpage__start_date__year__in=(2021, 2022)) |
        )

    All of these replacements would be combined into a new ``Q`` that
    looked something like this:

    .. code-block:: python

        Q(
            live=True,
            Q(
                Q(blogpage__popularity__gte=50) |
                Q(eventpage__popularity__gte=50) |
                Q(specialeventpage__popularity__gte=50) |
            ),
            Q(
                Q(eventpage__start_date__year__in=(2021, 2022)) |
                Q(specialeventpage__start_date__year__in=(2021, 2022)) |
            ),
        )

    Raises ``django.core.exceptions.FieldDoesNotExist`` if the provided model
    and it's concrete subclasses do not have any field matching those used in
    the lookups.

    Raises ``ValueError`` if the provided model has no concrete subclasses at
    all.
    """
    return_q = Q(_connector=original_q.connector, _negated=original_q.negated)

    for child in original_q.children:
        if isinstance(child, Q):
            # Recursively convert child Q objects
            return_q.children.append(get_subclass_spanning_q(model, child))
        else:
            lookup_key, value = child
            if has_field(model, lookup_key.split("__")[0]):
                # If `model` has this field, reuse the `child` as-is
                return_q.children.append(child)
            else:
                # Otherwise, replace `child` with a new table-spanning Q
                new_child = Q()

                for expanded_lookup_key in get_subclass_spanning_lookups(lookup_key):
                    new_child |= Q(**{expanded_lookup_key: value})
                return_q.children.append(new_child)

    return return_q


def get_subclass_spanning_lookups(
    model_class: ModelBase, lookup_key: str
) -> Tuple[str]:
    """
    Returns a tuple of strings that can be used in queries to access field values
    on concrete subclasses of model with fields named ``key``.

    For example, if ``key`` was ``"popularity__gte"``, and four subclasses of
    the supplied model existing with a field named ``popularity``, the return
    value might look something like this:

    .. code-block:: python

        (
            "blogpage__popularity__gte",
            "eventpage__popularity__gte",
            "specialeventpage__popularity__gte",
            "venuepage__popularity__gte",
        )
    """
    return tuple(
        f"{access_str}__{lookup_key}"
        for access_str in get_concrete_subclass_lookups(
            model_class, for_field=lookup_key.split("__")[0]
        ).values()
    )
