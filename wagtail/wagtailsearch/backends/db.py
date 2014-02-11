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
        pass # Not needed

    def delete(self, obj):
        pass # Not needed

    def search(self, query_string, model, fields=None, filters={}, prefetch_related=[]):
        # Get terms
        terms = query_string.split()
        if not terms:
            return model.objects.none()

        # Start will all objects
        query = model.objects.all()

        # Apply filters
        if filters:
            query = query.filter(**filters)

        # Filter by terms
        for term in terms:
            term_query = None
            for field_name in model.indexed_get_indexed_fields().keys():
                field_filter = {'%s__icontains' % field_name: term}
                if term_query is None:
                    term_query = models.Q(**field_filter)
                else:
                    term_query |= models.Q(**field_filter)
            query = query.filter(term_query)

        # Distinct
        query = query.distinct()

        # Prefetch related
        for prefetch in prefetch_related:
            query = query.prefetch_related(prefetch)

        return query