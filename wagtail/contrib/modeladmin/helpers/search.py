import operator
from functools import reduce

from django.contrib.admin.utils import lookup_needs_distinct
from django.db.models import Q

from wagtail.search.backends import get_search_backend


class ModelAdminSearchHandler:
    def __init__(self, queryset, search_fields):
        self.queryset = queryset
        self.search_fields = search_fields

    def search(self, search_term):
        """
        Returns a tuple containing a queryset to implement the search,
        and a boolean indicating if the results may contain duplicates.
        """
        raise NotImplementedError()


class DjangoORMSearchHandler(ModelAdminSearchHandler):
    def search(self, search_term):
        if not search_term or self.search_fields:
            return self.queryset
        use_distinct = False
        querset = self.queryset
        orm_lookups = ['%s__icontains' % str(search_field)
                       for search_field in self.search_fields]
        for bit in search_term.split():
            or_queries = [Q(**{orm_lookup: bit})
                          for orm_lookup in orm_lookups]
            querset = querset.filter(reduce(operator.or_, or_queries))
        opts = querset.model._meta
        for search_spec in orm_lookups:
            # Check wether out results may have duplicates, then remove them
            if lookup_needs_distinct(opts, search_spec):
                use_distinct = True
                break
        return querset, use_distinct


class WagtailBackendSearchHandler(ModelAdminSearchHandler):
    def search(self, search_term):
        backend = get_search_backend()
        if self.search_fields:
            return backend.search(search_term, self.queryset, fields=self.search_fields), False
        return backend.search(search_term, self.queryset), False
