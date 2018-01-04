from warnings import warn

from django.db import models
from django.db.models.expressions import Value

from wagtail.search.backends.base import (
    BaseSearchBackend, BaseSearchQueryCompiler, BaseSearchResults)
from wagtail.search.query import And, MatchAll, Not, Or, SearchQueryShortcut, Term
from wagtail.search.utils import AND, OR


class DatabaseSearchQueryCompiler(BaseSearchQueryCompiler):
    DEFAULT_OPERATOR = 'and'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields_names = list(self.get_fields_names())

    def get_fields_names(self):
        model = self.queryset.model
        fields_names = self.fields or [field.field_name for field in
                                       model.get_searchable_search_fields()]
        # Check if the field exists (this will filter out indexed callables)
        for field_name in fields_names:
            try:
                model._meta.get_field(field_name)
            except models.fields.FieldDoesNotExist:
                continue
            else:
                yield field_name

    def _process_lookup(self, field, lookup, value):
        return models.Q(**{field.get_attname(self.queryset.model) + '__' + lookup: value})

    def _connect_filters(self, filters, connector, negated):
        if connector == 'AND':
            q = models.Q(*filters)
        elif connector == 'OR':
            q = OR([models.Q(fil) for fil in filters])
        else:
            return

        if negated:
            q = ~q

        return q

    def build_single_term_filter(self, term):
        term_query = models.Q()
        for field_name in self.fields_names:
            term_query |= models.Q(**{field_name + '__icontains': term})
        return term_query

    def build_database_filter(self, query=None):
        if query is None:
            query = self.query

        if isinstance(self.query, MatchAll):
            return models.Q()

        if isinstance(query, SearchQueryShortcut):
            return self.build_database_filter(query.get_equivalent())
        if isinstance(query, Term):
            if query.boost != 1:
                warn('Database search backend does not support term boosting.')
            return self.build_single_term_filter(query.term)
        if isinstance(query, Not):
            return ~self.build_database_filter(query.subquery)
        if isinstance(query, And):
            return AND(self.build_database_filter(subquery)
                       for subquery in query.subqueries)
        if isinstance(query, Or):
            return OR(self.build_database_filter(subquery)
                      for subquery in query.subqueries)
        raise NotImplementedError(
            '`%s` is not supported by the database search backend.'
            % self.query.__class__.__name__)


class DatabaseSearchResults(BaseSearchResults):
    def get_queryset(self):
        queryset = self.query_compiler.queryset

        # Run _get_filters_from_queryset to test that no fields that are not
        # a FilterField have been used in the query.
        self.query_compiler._get_filters_from_queryset()

        q = self.query_compiler.build_database_filter()

        return queryset.filter(q).distinct()[self.start:self.stop]

    def _do_search(self):
        queryset = self.get_queryset()

        if self._score_field:
            queryset = queryset.annotate(**{self._score_field: Value(None, output_field=models.FloatField())})

        return queryset.iterator()

    def _do_count(self):
        return self.get_queryset().count()


class DatabaseSearchBackend(BaseSearchBackend):
    query_compiler_class = DatabaseSearchQueryCompiler
    results_class = DatabaseSearchResults

    def reset_index(self):
        pass  # Not needed

    def add_type(self, model):
        pass  # Not needed

    def refresh_index(self):
        pass  # Not needed

    def add(self, obj):
        pass  # Not needed

    def add_bulk(self, model, obj_list):
        return  # Not needed

    def delete(self, obj):
        pass  # Not needed


SearchBackend = DatabaseSearchBackend
