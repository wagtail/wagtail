from django.db import models

from wagtail.wagtailsearch.backends.base import BaseSearch
from wagtail.wagtailsearch.indexed import Indexed


class DBSearch(BaseSearch):
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

    def search(self, query_set, query_string, fields=None):
        # Model must be a descendant of Indexed
        if not issubclass(query_set.model, Indexed):
            return query_set.none()

        # Get terms
        terms = query_string.split()
        if not terms:
            return query_set.none()

        # Get fields
        if fields is None:
            fields = query_set.model._get_search_fields()[1].keys()

        # Return nothing if there are no fields
        if not fields:
            return query_set.none()

        # Filter by terms
        for term in terms:
            term_query = None
            for field_name in fields:
                # Check if the field exists (this will filter out indexed callables)
                try:
                    query_set.model._meta.get_field_by_name(field_name)
                except:
                    continue

                # Filter on this field
                field_filter = {'%s__icontains' % field_name: term}
                if term_query is None:
                    term_query = models.Q(**field_filter)
                else:
                    term_query |= models.Q(**field_filter)
            query_set = query_set.filter(term_query)

        return query_set
