from collections import OrderedDict
from warnings import warn

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import Count
from django.db.models.expressions import Value

from wagtail.search.backends.base import (
    BaseSearchBackend, BaseSearchQueryCompiler, BaseSearchResults, FilterFieldError)
from wagtail.search.query import And, Boost, MatchAll, Not, Or, Phrase, PlainText
from wagtail.search.utils import AND, OR


# This file implements a database search backend using basic substring matching, and no
# database-specific full-text search capabilities. It will be used in the following cases:
# * The current default database is SQLite <3.19, or something other than PostgreSQL, MySQL or
#   SQLite
# * 'wagtail.search.backends.database.fallback' is specified directly as the search backend
# * The deprecated 'wagtail.search.backends.db' backend is active; this is the default when no
#   WAGTAILSEARCH_BACKENDS setting is present.
#
# RemovedInWagtail217Warning - the default will be switched to wagtail.search.backends.database
# and wagtail.search.backends.db will be dropped.


MATCH_ALL = "_ALL_"
MATCH_NONE = "_NONE_"


class DatabaseSearchQueryCompiler(BaseSearchQueryCompiler):
    DEFAULT_OPERATOR = "and"
    OPERATORS = {
        "and": AND,
        "or": OR,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields_names = list(self.get_fields_names())

    def get_fields_names(self):
        model = self.queryset.model
        fields_names = self.fields or [
            field.field_name for field in model.get_searchable_search_fields()
        ]
        # Check if the field exists (this will filter out indexed callables)
        for field_name in fields_names:
            try:
                model._meta.get_field(field_name)
            except FieldDoesNotExist:
                continue
            else:
                yield field_name

    def _process_lookup(self, field, lookup, value):
        return models.Q(
            **{field.get_attname(self.queryset.model) + "__" + lookup: value}
        )

    def _connect_filters(self, filters, connector, negated):
        if connector == "AND":
            q = models.Q(*filters)
        elif connector == "OR":
            q = OR([models.Q(fil) for fil in filters])
        else:
            return

        if negated:
            q = ~q

        return q

    def build_single_term_filter(self, term):
        term_query = models.Q()
        for field_name in self.fields_names:
            term_query |= models.Q(**{field_name + "__icontains": term})
        return term_query

    def check_boost(self, query, boost=1.0):
        if query.boost * boost != 1.0:
            warn("Database search backend does not support term boosting.")

    def build_database_filter(self, query, boost=1.0):
        if isinstance(query, PlainText):
            self.check_boost(query, boost=boost)

            operator = self.OPERATORS[query.operator]

            return operator(
                [
                    self.build_single_term_filter(term)
                    for term in query.query_string.split()
                ]
            )

        if isinstance(query, Phrase):
            q = models.Q()
            for field_name in self.fields_names:
                q |= models.Q(**{field_name + "__icontains": query.query_string})
            return q

        if isinstance(query, Boost):
            boost *= query.boost
            return self.build_database_filter(query.subquery, boost=boost)

        if isinstance(query, MatchAll):
            return MATCH_ALL

        if isinstance(query, Not):
            q = self.build_database_filter(query.subquery, boost=boost)

            if q == MATCH_ALL:
                return MATCH_NONE

            elif q == MATCH_NONE:
                return MATCH_ALL

            else:
                return ~q

        if isinstance(query, And):
            subqueries = [
                self.build_database_filter(subquery, boost=boost)
                for subquery in query.subqueries
            ]

            # If there's a MATCH_NONE, return MATCH_NONE
            if MATCH_NONE in subqueries:
                return MATCH_NONE

            # Ignore MATCH_ALL
            subqueries = [q for q in subqueries if q != MATCH_ALL]

            return AND(subqueries)

        if isinstance(query, Or):
            subqueries = [
                self.build_database_filter(subquery, boost=boost)
                for subquery in query.subqueries
            ]

            # If there's a MATCH_ALL, return MATCH_ALL
            if MATCH_ALL in subqueries:
                return MATCH_ALL

            # Ignore MATCH_NONE
            subqueries = [q for q in subqueries if q != MATCH_NONE]

            return OR(subqueries)

        raise NotImplementedError(
            "`%s` is not supported by the database search backend."
            % query.__class__.__name__
        )


class DatabaseSearchResults(BaseSearchResults):
    def get_queryset(self):
        queryset = self.query_compiler.queryset

        # Run _get_filters_from_queryset to test that no fields that are not
        # a FilterField have been used in the query.
        self.query_compiler._get_filters_from_queryset()

        q = self.query_compiler.build_database_filter(self.query_compiler.query)

        if q == MATCH_ALL:
            pass
        elif q == MATCH_NONE:
            queryset = queryset.none()
        else:
            queryset = queryset.filter(q)

        return queryset.distinct()[self.start: self.stop]

    def _do_search(self):
        queryset = self.get_queryset()

        if self._score_field:
            queryset = queryset.annotate(
                **{self._score_field: Value(None, output_field=models.FloatField())}
            )

        return queryset.iterator()

    def _do_count(self):
        return self.get_queryset().count()

    supports_facet = True

    def facet(self, field_name):
        # Get field
        field = self.query_compiler._get_filterable_field(field_name)
        if field is None:
            raise FilterFieldError(
                'Cannot facet search results with field "'
                + field_name
                + "\". Please add index.FilterField('"
                + field_name
                + "') to "
                + self.query_compiler.queryset.model.__name__
                + ".search_fields.",
                field_name=field_name,
            )

        query = self.get_queryset()
        results = (
            query.values(field_name).annotate(count=Count("pk")).order_by("-count")
        )

        return OrderedDict(
            [(result[field_name], result["count"]) for result in results]
        )


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


# This line allows using 'wagtail.search.backends.database.fallback' as the backend, bypassing the automatic selection of the backend that would get run if the user chose 'wagtail.search.backends.database'
SearchBackend = DatabaseSearchBackend
