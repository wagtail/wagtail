from django.db import models

from wagtail.wagtailsearch.backends.base import BaseSearch, BaseSearchQuery, BaseSearchResults


class DBSearchQuery(BaseSearchQuery):
    def _process_lookup(self, field, lookup, value):
        return models.Q(**{field.get_attname(self.queryset.model) + '__' + lookup: value})

    def _connect_filters(self, filters, connector, negated):
        if connector == 'AND':
            q = models.Q(*filters)
        elif connector == 'OR':
            q = models.Q(filters[0])
            for fil in filters[1:]:
                q |= fil
        else:
            return

        if negated:
            q = ~q

        return q

    def get_q(self):
        # Get filters as a q object
        q = self._get_filters_from_queryset()

        model = self.queryset.model

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

                q &= term_query

        return q


class DBSearchResults(BaseSearchResults):
    def get_queryset(self):
        model = self.query.queryset.model
        q = self.query.get_q()

        return model.objects.filter(q).distinct()[self.start:self.stop]

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
