import copy

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import DEFERRED
from django.utils.functional import cached_property


class SpecificMixin:
    """
    Mixin for models that support multi-table inheritance and provide a
    ``content_type`` field pointing to the specific model class, to provide
    methods and properties for retrieving the specific instance of the model.
    """

    def _get_cached_specific_obj(self, model_class):
        """
        Return a pre-fetched ``model_class`` instance from ``_state.fields_cache``
        (e.g. populated by ``select_related()`` or ``prefetch_related()``) if present.
        """
        accessors = []
        curr = model_class
        base_cls = type(self)
        while curr is not base_cls:
            link = curr._meta.parents.get(base_cls)
            if link is not None:
                accessors.append(link.remote_field.get_accessor_name())
                break
            next_parent = None
            for parent, parent_link in curr._meta.parents.items():
                if issubclass(parent, base_cls) and parent_link is not None:
                    accessors.append(parent_link.remote_field.get_accessor_name())
                    next_parent = parent
                    break
            if next_parent is None:
                return None
            curr = next_parent

        obj = self
        for accessor in reversed(accessors):
            obj = obj._state.fields_cache.get(accessor)
            if obj is None:
                return None
        return obj if isinstance(obj, model_class) else None

    def _copy_relation_caches(
        self, specific_obj, model_class, cached_specific, exclude
    ):
        """
        Copy ``select_related()`` (``_state.fields_cache``) and
        ``prefetch_related()`` (``_prefetched_objects_cache``) caches onto
        ``specific_obj`` unless excluded.
        """
        if "_state" not in exclude:
            if cached_specific is not None:
                for k, v in cached_specific._state.fields_cache.items():
                    specific_obj._state.fields_cache.setdefault(k, v)

            for k, v in self._state.fields_cache.items():
                try:
                    field = model_class._meta.get_field(k)
                except FieldDoesNotExist:
                    continue
                if not (
                    isinstance(field, models.OneToOneRel)
                    and issubclass(field.related_model, type(self))
                ):
                    specific_obj._state.fields_cache.setdefault(k, v)

        if "_prefetched_objects_cache" not in exclude:
            prefetched = dict(getattr(specific_obj, "_prefetched_objects_cache", {}))
            if cached_specific is not None and hasattr(
                cached_specific, "_prefetched_objects_cache"
            ):
                for k, v in cached_specific._prefetched_objects_cache.items():
                    prefetched.setdefault(k, v)
            if hasattr(self, "_prefetched_objects_cache"):
                for k, v in self._prefetched_objects_cache.items():
                    prefetched.setdefault(k, v)
            if prefetched:
                specific_obj._prefetched_objects_cache = prefetched

    def get_specific(self, deferred=False, copy_attrs=None, copy_attrs_exclude=None):
        """
        Return this object in its most specific subclassed form.

        By default, a database query is made to fetch all field values for the
        specific object. If you only require access to custom methods or other
        non-field attributes on the specific object, you can use
        ``deferred=True`` to avoid this query. However, any attempts to access
        specific field values from the returned object will trigger additional
        database queries.

        By default, references to all non-field attribute values are copied
        from current object to the returned one. This includes:

        * Values set by a queryset, for example: annotations, or values set as
          a result of using ``select_related()`` or ``prefetch_related()``.
        * Any ``cached_property`` values that have been evaluated.
        * Attributes set elsewhere in Python code.

        For fine-grained control over which non-field values are copied to the
        returned object, you can use ``copy_attrs`` to specify a complete list
        of attribute names to include. Alternatively, you can use
        ``copy_attrs_exclude`` to specify a list of attribute names to exclude.

        If called on an object that is already an instance of the most specific
        class, the object will be returned as is, and no database queries or
        other operations will be triggered.

        If the object was originally created using a model that has since
        been removed from the codebase, an instance of the base class will be
        returned (without any custom field values or other functionality
        present on the original class). Usually, deleting these objects is the
        best course of action, but there is currently no safe way for Wagtail
        to do that at migration time.
        """
        model_class = self.specific_class

        if model_class is None:
            # The codebase and database are out of sync (e.g. the model exists
            # on a different git branch and migrations were not applied or
            # reverted before switching branches). So, the best we can do is
            # return the page in it's current form.
            return self

        if isinstance(self, model_class):
            # self is already an instance of the most specific class.
            return self

        cached_specific = self._get_cached_specific_obj(model_class)

        if deferred:
            # Generate a tuple of values in the order expected by __init__(),
            # with missing values substituted with DEFERRED ()
            values = tuple(
                getattr(self, f.attname, self.pk if f.primary_key else DEFERRED)
                for f in model_class._meta.concrete_fields
            )
            # Create object from known attribute values
            specific_obj = model_class(*values)
            specific_obj._state.adding = self._state.adding
        elif cached_specific is not None and not cached_specific.get_deferred_fields():
            # Reuse the specific instance already loaded via select_related/prefetch_related
            specific_obj = copy.copy(cached_specific)
            specific_obj._state = copy.copy(cached_specific._state)
            specific_obj._state.fields_cache = (
                cached_specific._state.fields_cache.copy()
            )
            if hasattr(cached_specific, "_prefetched_objects_cache"):
                specific_obj._prefetched_objects_cache = (
                    cached_specific._prefetched_objects_cache.copy()
                )
        else:
            # Fetch object from database
            specific_obj = model_class._default_manager.get(id=self.id)

        # Copy non-field attribute values
        if copy_attrs is not None:
            for attr in (attr for attr in copy_attrs if attr in self.__dict__):
                setattr(specific_obj, attr, getattr(self, attr))
        else:
            exclude = set(copy_attrs_exclude or ())
            for k, v in self.__dict__.items():
                if k not in exclude and k not in (
                    "_state",
                    "_prefetched_objects_cache",
                ):
                    # only set values that haven't already been set
                    specific_obj.__dict__.setdefault(k, v)
            self._copy_relation_caches(
                specific_obj, model_class, cached_specific, exclude
            )

        return specific_obj

    @cached_property
    def specific(self):
        """
        Returns this object in its most specific subclassed form with all field
        values fetched from the database. The result is cached in memory.
        """
        return self.get_specific()

    @cached_property
    def specific_deferred(self):
        """
        Returns this object in its most specific subclassed form without any
        additional field values being fetched from the database. The result
        is cached in memory.
        """
        return self.get_specific(deferred=True)

    @cached_property
    def specific_class(self):
        """
        Return the class that this object would be if instantiated in its
        most specific form.

        If the model class can no longer be found in the codebase, and the
        relevant ``ContentType`` has been removed by a database migration,
        the return value will be ``None``.

        If the model class can no longer be found in the codebase, but the
        relevant ``ContentType`` is still present in the database (usually a
        result of switching between git branches without running or reverting
        database migrations beforehand), the return value will be ``None``.
        """
        return self.cached_content_type.model_class()

    @property
    def cached_content_type(self):
        """
        Return this object's ``content_type`` value from the ``ContentType``
        model's cached manager, which will avoid a database query if the
        content type is already in memory.
        """
        return ContentType.objects.get_for_id(self.content_type_id)
