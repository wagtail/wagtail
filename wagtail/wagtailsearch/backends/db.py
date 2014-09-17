from django.db import models

from wagtail.wagtailsearch.backends.base import BaseSearch, BaseSearchResults


class DBSearchQuery(object):
    def __init__(self, queryset, query_string, fields=None):
        self.queryset = queryset
        self.query_string = query_string
        self.fields = fields

    def get_queryset(self):
        queryset = self.queryset
        model = queryset.model

        if self.query_string is not None:
            # Get fields
            fields = self.fields or [field.field_name for field in model.get_searchable_search_fields()]

            # Get terms
            terms = self.query_string.split()
            if not terms:
                return model.objects.none()

            # Filter by terms
            for term in terms:
                term_query = models.Q()
                for field_name in fields:
                    # Check if the field exists (this will filter out indexed callables)
                    try:
                        model._meta.get_field_by_name(field_name)
                    except:
                        continue

                    # Filter on this field
                    term_query |= models.Q(**{'%s__icontains' % field_name: term})

                queryset = queryset.filter(term_query)

            # Distinct
            queryset = queryset.distinct()

        return queryset


class DBSearchResults(BaseSearchResults):
    def get_queryset(self):
        return self.query.get_queryset()[self.start:self.stop]

    def _do_search(self):
        return self.get_queryset()

    def _do_count(self):
        return self.get_queryset().count()


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

    def add_bulk(self, model, obj_list):
        return # Not needed

    def delete(self, obj):
        pass # Not needed

    def _search(self, queryset, query_string, fields=None):
        return DBSearchResults(self, DBSearchQuery(queryset, query_string, fields=fields))
