import operator
from functools import reduce

from django.contrib.admin.utils import lookup_needs_distinct
from django.db.models import Q

from wagtail.search.backends import get_search_backend


class ModelAdminSearchHandler:
    def __init__(self, search_fields):
        self.search_fields = search_fields

    def do_search(self, queryset, search_term, **kwargs):
        """
        Returns a tuple containing a queryset to implement the search,
        and a boolean indicating if the results may contain duplicates.
        """
        raise NotImplementedError()

    @property
    def show_search_form(self):
        """
        Defines whether this SearchHandler should show the search form on
        the index page.
        """
        return True


class DjangoORMSearchHandler(ModelAdminSearchHandler):
    def do_search(self, queryset, search_term):
        if not search_term or not self.search_fields:
            return queryset, False
        use_distinct = False
        orm_lookups = ['%s__icontains' % str(search_field)
                       for search_field in self.search_fields]
        for bit in search_term.split():
            or_queries = [Q(**{orm_lookup: bit})
                          for orm_lookup in orm_lookups]
            queryset = queryset.filter(reduce(operator.or_, or_queries))
        opts = queryset.model._meta
        for search_spec in orm_lookups:
            # Check wether out results may have duplicates, then remove them
            if lookup_needs_distinct(opts, search_spec):
                use_distinct = True
                break
        return queryset, use_distinct

    @property
    def show_search_form(self):
        return bool(self.search_fields)


class WagtailBackendSearchHandler(ModelAdminSearchHandler):
    def do_search(self, queryset, search_term, backend='default'):
        if not search_term:
            return queryset, False
        backend = get_search_backend(backend)
        if self.search_fields:
            return backend.search(search_term, queryset, fields=self.search_fields), False
        return backend.search(search_term, queryset), False
