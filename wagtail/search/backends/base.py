import datetime
from warnings import warn

from django.db.models.functions.datetime import Extract as ExtractDate
from django.db.models.functions.datetime import ExtractYear
from django.db.models.lookups import Lookup
from django.db.models.query import QuerySet
from django.db.models.sql.where import SubqueryConstraint, WhereNode

from wagtail.search.index import class_is_indexed, get_indexed_models
from wagtail.search.query import MATCH_ALL, PlainText
from wagtail.utils.deprecation import RemovedInWagtail60Warning


class FilterError(Exception):
    pass


class FieldError(Exception):
    def __init__(self, *args, field_name=None, **kwargs):
        self.field_name = field_name
        super().__init__(*args, **kwargs)


class SearchFieldError(FieldError):
    pass


class FilterFieldError(FieldError):
    pass


class OrderByFieldError(FieldError):
    pass


class BaseSearchQueryCompiler:
    DEFAULT_OPERATOR = "or"

    def __init__(
        self,
        queryset,
        query,
        fields=None,
        operator=None,
        order_by_relevance=True,
        partial_match=None,  # RemovedInWagtail60Warning
    ):
        self.queryset = queryset
        if query is None:
            warn(
                "Querying `None` is deprecated, use `MATCH_ALL` instead.",
                DeprecationWarning,
            )
            query = MATCH_ALL
        elif isinstance(query, str):
            query = PlainText(query, operator=operator or self.DEFAULT_OPERATOR)
        self.query = query
        self.fields = fields
        self.order_by_relevance = order_by_relevance
        if partial_match:
            warn(
                "The partial_match=True argument on `search` is no longer supported. "
                "Use the `autocomplete` method instead",
                category=RemovedInWagtail60Warning,
            )
        elif partial_match is not None:
            warn(
                "The partial_match=False argument on `search` is no longer required "
                "and should be removed",
                category=RemovedInWagtail60Warning,
            )

    def _get_filterable_field(self, field_attname):
        # Get field
        field = {
            field.get_attname(self.queryset.model): field
            for field in self.queryset.model.get_filterable_search_fields()
        }.get(field_attname, None)

        return field

    def _process_lookup(self, field, lookup, value):
        raise NotImplementedError

    def _connect_filters(self, filters, connector, negated):
        raise NotImplementedError

    def _process_filter(self, field_attname, lookup, value, check_only=False):
        # Get the field
        field = self._get_filterable_field(field_attname)

        if field is None:
            raise FilterFieldError(
                'Cannot filter search results with field "'
                + field_attname
                + "\". Please add index.FilterField('"
                + field_attname
                + "') to "
                + self.queryset.model.__name__
                + ".search_fields.",
                field_name=field_attname,
            )

        # Process the lookup
        if not check_only:
            result = self._process_lookup(field, lookup, value)

        if result is None:
            raise FilterError(
                'Could not apply filter on search results: "'
                + field_attname
                + "__"
                + lookup
                + " = "
                + str(value)
                + '". Lookup "'
                + lookup
                + '"" not recognised.'
            )

        return result

    def _get_filters_from_where_node(self, where_node, check_only=False):
        # Check if this is a leaf node
        if isinstance(where_node, Lookup):
            if isinstance(where_node.lhs, ExtractDate):
                if not isinstance(where_node.lhs, ExtractYear):
                    raise FilterError(
                        'Cannot apply filter on search results: "'
                        + where_node.lhs.lookup_name
                        + '" queries are not supported.'
                    )
                else:
                    field_attname = where_node.lhs.lhs.target.attname
                    lookup = where_node.lookup_name
                    if lookup == "gte":
                        # filter on year(date) >= value
                        # i.e. date >= Jan 1st of that year
                        value = datetime.date(int(where_node.rhs), 1, 1)
                    elif lookup == "gt":
                        # filter on year(date) > value
                        # i.e. date >= Jan 1st of the next year
                        value = datetime.date(int(where_node.rhs) + 1, 1, 1)
                        lookup = "gte"
                    elif lookup == "lte":
                        # filter on year(date) <= value
                        # i.e. date < Jan 1st of the next year
                        value = datetime.date(int(where_node.rhs) + 1, 1, 1)
                        lookup = "lt"
                    elif lookup == "lt":
                        # filter on year(date) < value
                        # i.e. date < Jan 1st of that year
                        value = datetime.date(int(where_node.rhs), 1, 1)
                    elif lookup == "exact":
                        # filter on year(date) == value
                        # i.e. date >= Jan 1st of that year and date < Jan 1st of the next year
                        filter1 = self._process_filter(
                            field_attname,
                            "gte",
                            datetime.date(int(where_node.rhs), 1, 1),
                            check_only=check_only,
                        )
                        filter2 = self._process_filter(
                            field_attname,
                            "lt",
                            datetime.date(int(where_node.rhs) + 1, 1, 1),
                            check_only=check_only,
                        )
                        if check_only:
                            return
                        else:
                            return self._connect_filters(
                                [filter1, filter2], "AND", False
                            )
                    else:
                        raise FilterError(
                            'Cannot apply filter on search results: "'
                            + where_node.lhs.lookup_name
                            + '" queries are not supported.'
                        )
            else:
                field_attname = where_node.lhs.target.attname
                lookup = where_node.lookup_name
                value = where_node.rhs

            # Ignore pointer fields that show up in specific page type queries
            if field_attname.endswith("_ptr_id"):
                return

            # Process the filter
            return self._process_filter(
                field_attname, lookup, value, check_only=check_only
            )

        elif isinstance(where_node, SubqueryConstraint):
            raise FilterError(
                "Could not apply filter on search results: Subqueries are not allowed."
            )

        elif isinstance(where_node, WhereNode):
            # Get child filters
            connector = where_node.connector
            child_filters = [
                self._get_filters_from_where_node(child)
                for child in where_node.children
            ]

            if not check_only:
                child_filters = [
                    child_filter for child_filter in child_filters if child_filter
                ]
                return self._connect_filters(
                    child_filters, connector, where_node.negated
                )

        else:
            raise FilterError(
                "Could not apply filter on search results: Unknown where node: "
                + str(type(where_node))
            )

    def _get_filters_from_queryset(self):
        return self._get_filters_from_where_node(self.queryset.query.where)

    def _get_order_by(self):
        if self.order_by_relevance:
            return

        for field_name in self.queryset.query.order_by:
            reverse = False

            if field_name.startswith("-"):
                reverse = True
                field_name = field_name[1:]

            field = self._get_filterable_field(field_name)

            if field is None:
                raise OrderByFieldError(
                    'Cannot sort search results with field "'
                    + field_name
                    + "\". Please add index.FilterField('"
                    + field_name
                    + "') to "
                    + self.queryset.model.__name__
                    + ".search_fields.",
                    field_name=field_name,
                )

            yield reverse, field

    def check(self):
        # Check search fields
        if self.fields:
            allowed_fields = {
                field.field_name
                for field in self.queryset.model.get_searchable_search_fields()
            }

            for field_name in self.fields:
                if field_name not in allowed_fields:
                    raise SearchFieldError(
                        'Cannot search with field "'
                        + field_name
                        + "\". Please add index.SearchField('"
                        + field_name
                        + "') to "
                        + self.queryset.model.__name__
                        + ".search_fields.",
                        field_name=field_name,
                    )

        # Check where clause
        # Raises FilterFieldError if an unindexed field is being filtered on
        self._get_filters_from_where_node(self.queryset.query.where, check_only=True)

        # Check order by
        # Raises OrderByFieldError if an unindexed field is being used to order by
        list(self._get_order_by())


class BaseSearchResults:
    supports_facet = False

    def __init__(self, backend, query_compiler, prefetch_related=None):
        self.backend = backend
        self.query_compiler = query_compiler
        self.prefetch_related = prefetch_related
        self.start = 0
        self.stop = None
        self._results_cache = None
        self._count_cache = None
        self._score_field = None

    def _set_limits(self, start=None, stop=None):
        if stop is not None:
            if self.stop is not None:
                self.stop = min(self.stop, self.start + stop)
            else:
                self.stop = self.start + stop

        if start is not None:
            if self.stop is not None:
                self.start = min(self.stop, self.start + start)
            else:
                self.start = self.start + start

    def _clone(self):
        klass = self.__class__
        new = klass(
            self.backend, self.query_compiler, prefetch_related=self.prefetch_related
        )
        new.start = self.start
        new.stop = self.stop
        new._score_field = self._score_field
        return new

    def _do_search(self):
        raise NotImplementedError

    def _do_count(self):
        raise NotImplementedError

    def results(self):
        if self._results_cache is None:
            self._results_cache = list(self._do_search())
        return self._results_cache

    def count(self):
        if self._count_cache is None:
            if self._results_cache is not None:
                self._count_cache = len(self._results_cache)
            else:
                self._count_cache = self._do_count()
        return self._count_cache

    def __getitem__(self, key):
        new = self._clone()

        if isinstance(key, slice):
            # Set limits
            start = int(key.start) if key.start is not None else None
            stop = int(key.stop) if key.stop is not None else None
            new._set_limits(start, stop)

            # Copy results cache
            if self._results_cache is not None:
                new._results_cache = self._results_cache[key]

            return new
        else:
            if self._results_cache is not None:
                return self._results_cache[key]

            new.start = self.start + key
            new.stop = self.start + key + 1
            return list(new)[0]

    def __iter__(self):
        return iter(self.results())

    def __len__(self):
        return len(self.results())

    def __repr__(self):
        data = list(self[:21])
        if len(data) > 20:
            data[-1] = "...(remaining elements truncated)..."
        return "<SearchResults %r>" % data

    def annotate_score(self, field_name):
        clone = self._clone()
        clone._score_field = field_name
        return clone

    def facet(self, field_name):
        raise NotImplementedError("This search backend does not support faceting")


class EmptySearchResults(BaseSearchResults):
    def __init__(self):
        super().__init__(None, None)

    def _clone(self):
        return self.__class__()

    def _do_search(self):
        return []

    def _do_count(self):
        return 0


class NullIndex:
    """
    Index class that provides do-nothing implementations of the indexing operations required by
    BaseSearchBackend. Use this for search backends that do not maintain an index, such as the
    database backend.
    """

    def add_model(self, model):
        pass

    def refresh(self):
        pass

    def add_item(self, item):
        pass

    def add_items(self, model, items):
        pass

    def delete_item(self, item):
        pass


class BaseSearchBackend:
    query_compiler_class = None
    autocomplete_query_compiler_class = None
    results_class = None
    rebuilder_class = None
    catch_indexing_errors = False

    def __init__(self, params):
        pass

    def get_index_for_model(self, model):
        return NullIndex()

    def get_rebuilder(self):
        return None

    def reset_index(self):
        raise NotImplementedError

    def add_type(self, model):
        self.get_index_for_model(model).add_model(model)

    def refresh_index(self):
        refreshed_indexes = []
        for model in get_indexed_models():
            index = self.get_index_for_model(model)
            if index not in refreshed_indexes:
                index.refresh()
                refreshed_indexes.append(index)

    def add(self, obj):
        self.get_index_for_model(type(obj)).add_item(obj)

    def add_bulk(self, model, obj_list):
        self.get_index_for_model(model).add_items(model, obj_list)

    def delete(self, obj):
        self.get_index_for_model(type(obj)).delete_item(obj)

    def _search(self, query_compiler_class, query, model_or_queryset, **kwargs):
        # Find model/queryset
        if isinstance(model_or_queryset, QuerySet):
            model = model_or_queryset.model
            queryset = model_or_queryset
        else:
            model = model_or_queryset
            queryset = model_or_queryset.objects.all()

        # Model must be a class that is in the index
        if not class_is_indexed(model):
            return EmptySearchResults()

        # Check that there's still a query string after the clean up
        if query == "":
            return EmptySearchResults()

        # Search
        search_query_compiler = query_compiler_class(queryset, query, **kwargs)

        # Check the query
        search_query_compiler.check()

        return self.results_class(self, search_query_compiler)

    def search(
        self,
        query,
        model_or_queryset,
        fields=None,
        operator=None,
        order_by_relevance=True,
        partial_match=None,  # RemovedInWagtail60Warning
    ):
        return self._search(
            self.query_compiler_class,
            query,
            model_or_queryset,
            fields=fields,
            operator=operator,
            order_by_relevance=order_by_relevance,
            partial_match=partial_match,  # RemovedInWagtail60Warning
        )

    def autocomplete(
        self,
        query,
        model_or_queryset,
        fields=None,
        operator=None,
        order_by_relevance=True,
    ):
        if self.autocomplete_query_compiler_class is None:
            raise NotImplementedError(
                "This search backend does not support the autocomplete API"
            )

        return self._search(
            self.autocomplete_query_compiler_class,
            query,
            model_or_queryset,
            fields=fields,
            operator=operator,
            order_by_relevance=order_by_relevance,
        )
