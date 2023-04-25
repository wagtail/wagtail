import operator
from functools import reduce

from django.db.models import Q

from wagtail.search.backends import get_search_backend

try:
    from django.contrib.admin.utils import lookup_spawns_duplicates
except ImportError:
    # fallback for Django <4.0
    from django.contrib.admin.utils import (
        lookup_needs_distinct as lookup_spawns_duplicates,
    )


class BaseSearchHandler:
    def __init__(self, search_fields):
        self.search_fields = search_fields

    def search_queryset(self, queryset, search_term, **kwargs):
        """
        Returns an iterable of objects from ``queryset`` matching the
        provided ``search_term``.
        """
        raise NotImplementedError()

    @property
    def show_search_form(self):
        """
        Returns a boolean that determines whether a search form should be
        displayed in the IndexView UI.
        """
        return True


class DjangoORMSearchHandler(BaseSearchHandler):
    def search_queryset(self, queryset, search_term, **kwargs):
        if not search_term or not self.search_fields:
            return queryset

        orm_lookups = [
            "%s__icontains" % str(search_field) for search_field in self.search_fields
        ]
        for bit in search_term.split():
            or_queries = [Q(**{orm_lookup: bit}) for orm_lookup in orm_lookups]
            queryset = queryset.filter(reduce(operator.or_, or_queries))
        opts = queryset.model._meta
        for search_spec in orm_lookups:
            if lookup_spawns_duplicates(opts, search_spec):
                return queryset.distinct()
        return queryset

    @property
    def show_search_form(self):
        return bool(self.search_fields)


class WagtailBackendSearchHandler(BaseSearchHandler):

    default_search_backend = "default"

    def search_queryset(
        self,
        queryset,
        search_term,
        preserve_order=False,
        operator=None,
        backend=None,
        **kwargs,
    ):
        if not search_term:
            return queryset

        backend = get_search_backend(backend or self.default_search_backend)
        return backend.search(
            search_term,
            queryset,
            fields=self.search_fields or None,
            operator=operator,
            order_by_relevance=not preserve_order,
        )
