from django.db.models.query import QuerySet
from django.core.exceptions import ImproperlyConfigured

from wagtail.wagtailsearch.index import class_is_indexed
from wagtail.wagtailsearch.utils import normalise_query_string


class BaseSearch(object):
    def __init__(self, params):
        pass

    def reset_index(self):
        return NotImplemented

    def add_type(self, model):
        return NotImplemented

    def refresh_index(self):
        return NotImplemented

    def add(self, obj):
        return NotImplemented

    def add_bulk(self, model, obj_list):
        return NotImplemented

    def delete(self, obj):
        return NotImplemented

    def _search(self, queryset, query_string, fields=None):
        return NotImplemented

    def search(self, query_string, model_or_queryset, fields=None, filters=None, prefetch_related=None):
        # Find model/queryset
        if isinstance(model_or_queryset, QuerySet):
            model = model_or_queryset.model
            queryset = model_or_queryset
        else:
            model = model_or_queryset
            queryset = model_or_queryset.objects.all()

        # Model must be a class that is in the index
        if not class_is_indexed(model):
            return []

        # Normalise query string
        if query_string is not None:
            query_string = normalise_query_string(query_string)

        # Check that theres still a query string after the clean up
        if query_string == "":
            return []

        # Apply filters to queryset
        if filters:
            queryset = queryset.filter(**filters)

        # Prefetch related
        if prefetch_related:
            for prefetch in prefetch_related:
                queryset = queryset.prefetch_related(prefetch)

        # Search
        return self._search(queryset, query_string, fields=fields)
