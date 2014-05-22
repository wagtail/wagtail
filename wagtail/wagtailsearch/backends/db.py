from django.db import models

from wagtail.wagtailsearch.backends.base import BaseSearch, BaseSearchResults
from wagtail.wagtailsearch.indexed import Indexed


class DBSearchResults(BaseSearchResults):
    def _do_search(self):
        queryset = self.queryset

        # Get terms
        terms = self.query_string.split()
        if not terms:
            return queryset.none()

        # Get fields
        fields = self.fields
        if fields is None:
            fields = queryset.model.get_search_fields(exclude_filter=True).keys()

        # Filter by terms
        for term in terms:
            term_query = None
            for field_name in fields:
                # Check if the field exists (this will filter out indexed callables)
                try:
                    queryset.model._meta.get_field_by_name(field_name)
                except:
                    continue

                # Filter on this field
                field_filter = {'%s__icontains' % field_name: term}
                if term_query is None:
                    term_query = models.Q(**field_filter)
                else:
                    term_query |= models.Q(**field_filter)
            queryset = queryset.filter(term_query)

        return queryset[slice(self.start, self.stop)]

    def _do_count(self):
        return self._do_search().count()


class DBSearch(BaseSearch):
    results_class = DBSearchResults

    def __init__(self, params):
        super(DBSearch, self).__init__(params)

    def reset_index(self):
        pass # Not needed

    def add_type(self, model):
        pass # Not needed

    def refresh_index(self):
        pass # Not needed

    def add(self, obj):
        pass # Not needed

    def add_bulk(self, obj_list):
        return [] # Not needed

    def delete(self, obj):
        pass # Not needed
