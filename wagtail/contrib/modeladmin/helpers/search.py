import operator
from functools import reduce

from django.contrib.admin.utils import lookup_needs_distinct
from django.db.models import Q

from wagtail.search.backends import get_search_backend


class BaseSearchHandler:
    def __init__(self, search_fields):
        self.search_fields = search_fields

    def search_queryset(self, queryset, search_term, **kwargs):
        """
        Search the queryset for the provided term.
        """
        raise NotImplementedError()

    @property
    def show_search_form(self):
        """
        Returns a boolean that determines whether a search form should be
        displayed in the IndexView UI
        """
        return True


class DjangoORMSearchHandler(BaseSearchHandler):
    def search_queryset(self, queryset, search_term, distinct_applied=False, **kwargs):
        if not search_term or not self.search_fields:
            return queryset

        orm_lookups = ['%s__icontains' % str(search_field)
                       for search_field in self.search_fields]
        for bit in search_term.split():
            or_queries = [Q(**{orm_lookup: bit})
                          for orm_lookup in orm_lookups]
            queryset = queryset.filter(reduce(operator.or_, or_queries))
        opts = queryset.model._meta
        if not distinct_applied:
            for search_spec in orm_lookups:
                if lookup_needs_distinct(opts, search_spec):
                    return queryset.distinct()
        return queryset


    @property
    def show_search_form(self):
        return bool(self.search_fields)


class WagtailBackendSearchHandler(BaseSearchHandler):
    def search_queryset(self, queryset, search_term, operator=None, order_by_relevance=False,
                        partial_match=True, backend='default', **kwargs):
        if not search_term:
            return queryset
        backend = get_search_backend(backend)
        if self.search_fields:
            return backend.search(
                search_term, queryset, fields=self.search_fields, operator=operator,
                partial_match=partial_match, order_by_relevance=order_by_relevance)
        return backend.search(search_term, queryset)
