from collections import OrderedDict
from functools import reduce

from django.contrib.postgres.search import SearchRank, SearchVector
from django.db import DEFAULT_DB_ALIAS, NotSupportedError, connections, transaction
from django.db.models import Count, F, Manager, Q, TextField, Value
from django.db.models.constants import LOOKUP_SEP
from django.db.models.functions import Cast
from django.db.models.sql.subqueries import InsertQuery
from django.utils.encoding import force_str
from django.utils.functional import cached_property

from wagtail.search.backends.base import (
    BaseSearchBackend, BaseSearchQueryCompiler, BaseSearchResults, FilterFieldError)
from wagtail.search.index import RelatedFields, SearchField, get_indexed_models
from wagtail.search.query import And, Boost, MatchAll, Not, Or, PlainText
from wagtail.search.utils import ADD, MUL, OR

from .models import IndexEntry
from .query import Lexeme, RawSearchQuery
from .utils import (
    get_content_type_pk, get_descendants_content_types_pks, get_postgresql_connections,
    get_sql_weights, get_weight)

EMPTY_VECTOR = SearchVector(Value('', output_field=TextField()))


class ObjectIndexer:
    """
    Responsible for extracting data from an object to be inserted into the index.
    """
    def __init__(self, obj, search_config):
        self.obj = obj
        self.search_fields = obj.get_search_fields()
        self.search_config = search_config

    def prepare_value(self, value):
        if isinstance(value, str):
            return value

        elif isinstance(value, list):
            return ', '.join(self.prepare_value(item) for item in value)

        elif isinstance(value, dict):
            return ', '.join(self.prepare_value(item)
                             for item in value.values())

        return force_str(value)

    def prepare_field(self, obj, field):
        if isinstance(field, SearchField):
            yield (field, get_weight(field.boost),
                   self.prepare_value(field.get_value(obj)))

        elif isinstance(field, RelatedFields):
            sub_obj = field.get_value(obj)
            if sub_obj is None:
                return

            if isinstance(sub_obj, Manager):
                sub_objs = sub_obj.all()

            else:
                if callable(sub_obj):
                    sub_obj = sub_obj()

                sub_objs = [sub_obj]

            for sub_obj in sub_objs:
                for sub_field in field.fields:
                    yield from self.prepare_field(sub_obj, sub_field)

    def as_vector(self, texts):
        """
        Converts an array of strings into a SearchVector that can be indexed.
        """
        if not texts:
            return EMPTY_VECTOR

        return ADD([
            SearchVector(Value(text, output_field=TextField()), weight=weight, config=self.search_config)
            for text, weight in texts
        ])

    @cached_property
    def id(self):
        """
        Returns the value to use as the ID of the record in the index
        """
        return force_str(self.obj.pk)

    @cached_property
    def body(self):
        """
        Returns all values to index as "body". This is the value of all SearchFields that have partial_match=False
        """
        texts = []
        for field in self.search_fields:
            for current_field, boost, value in self.prepare_field(self.obj, field):
                if isinstance(current_field, SearchField) and not current_field.partial_match:
                    texts.append((value, boost))

        return self.as_vector(texts)

    @cached_property
    def autocomplete(self):
        """
        Returns all values to index as "autocomplete". This is the value of all SearchFields that have partial_match=True
        """
        texts = []
        for field in self.search_fields:
            for current_field, boost, value in self.prepare_field(self.obj, field):
                if isinstance(current_field, SearchField) and current_field.partial_match:
                    texts.append((value, boost))

        return self.as_vector(texts)


class Index:
    def __init__(self, backend, db_alias=None):
        self.backend = backend
        self.name = self.backend.index_name
        self.db_alias = DEFAULT_DB_ALIAS if db_alias is None else db_alias
        self.connection = connections[self.db_alias]
        if self.connection.vendor != 'postgresql':
            raise NotSupportedError(
                'You must select a PostgreSQL database '
                'to use PostgreSQL search.')

        # Whether to allow adding items via the faster upsert method available in Postgres >=9.5
        self._enable_upsert = (self.connection.pg_version >= 90500)

        self.entries = IndexEntry._default_manager.using(self.db_alias)

    def add_model(self, model):
        pass

    def refresh(self):
        pass

    def delete_stale_model_entries(self, model):
        existing_pks = (
            model._default_manager.using(self.db_alias)
            .annotate(object_id=Cast('pk', TextField()))
            .values('object_id')
        )
        content_types_pks = get_descendants_content_types_pks(model)
        stale_entries = (
            self.entries.filter(content_type_id__in=content_types_pks)
            .exclude(object_id__in=existing_pks)
        )
        stale_entries.delete()

    def delete_stale_entries(self):
        for model in get_indexed_models():
            # We don’t need to delete stale entries for non-root models,
            # since we already delete them by deleting roots.
            if not model._meta.parents:
                self.delete_stale_model_entries(model)

    def add_item(self, obj):
        self.add_items(obj._meta.model, [obj])

    def add_items_upsert(self, content_type_pk, indexers):
        compiler = InsertQuery(IndexEntry).get_compiler(connection=self.connection)
        autocomplete_sql = []
        body_sql = []
        data_params = []

        for indexer in indexers:
            data_params.extend((content_type_pk, indexer.id))

            # Compile autocomplete value
            value = compiler.prepare_value(IndexEntry._meta.get_field('autocomplete'), indexer.autocomplete)
            sql, params = value.as_sql(compiler, self.connection)
            autocomplete_sql.append(sql)
            data_params.extend(params)

            # Compile body value
            value = compiler.prepare_value(IndexEntry._meta.get_field('body'), indexer.body)
            sql, params = value.as_sql(compiler, self.connection)
            body_sql.append(sql)
            data_params.extend(params)

        data_sql = ', '.join([
            '(%%s, %%s, %s, %s)' % (a, b)
            for a, b in zip(autocomplete_sql, body_sql)
        ])

        with self.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO %s (content_type_id, object_id, autocomplete, body)
                (VALUES %s)
                ON CONFLICT (content_type_id, object_id)
                DO UPDATE SET autocomplete = EXCLUDED.autocomplete,
                              body = EXCLUDED.body
                """ % (IndexEntry._meta.db_table, data_sql), data_params)

    def add_items_update_then_create(self, content_type_pk, indexers):
        ids_and_data = {}
        for indexer in indexers:
            ids_and_data[indexer.id] = (indexer.autocomplete, indexer.body)

        index_entries_for_ct = self.entries.filter(content_type_id=content_type_pk)
        indexed_ids = frozenset(
            index_entries_for_ct.filter(object_id__in=ids_and_data.keys()).values_list('object_id', flat=True)
        )
        for indexed_id in indexed_ids:
            autocomplete, body = ids_and_data[indexed_id]
            index_entries_for_ct.filter(object_id=indexed_id).update(autocomplete=autocomplete, body=body)

        to_be_created = []
        for object_id in ids_and_data.keys():
            if object_id not in indexed_ids:
                autocomplete, body = ids_and_data[object_id]
                to_be_created.append(IndexEntry(
                    content_type_id=content_type_pk,
                    object_id=object_id,
                    autocomplete=autocomplete,
                    body=body
                ))

        self.entries.bulk_create(to_be_created)

    def add_items(self, model, objs):
        search_fields = model.get_search_fields()
        if not search_fields:
            return

        indexers = [ObjectIndexer(obj, self.backend.config) for obj in objs]

        # TODO: Delete unindexed objects while dealing with proxy models.
        if indexers:
            content_type_pk = get_content_type_pk(model)

            update_method = (
                self.add_items_upsert if self._enable_upsert
                else self.add_items_update_then_create)
            update_method(content_type_pk, indexers)

    def delete_item(self, item):
        item.index_entries.using(self.db_alias).delete()

    def __str__(self):
        return self.name


class PostgresSearchQueryCompiler(BaseSearchQueryCompiler):
    DEFAULT_OPERATOR = 'and'
    LAST_TERM_IS_PREFIX = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.search_fields = self.queryset.model.get_searchable_search_fields()

        # Due to a Django bug, arrays are not automatically converted
        # when we use WEIGHTS_VALUES.
        self.sql_weights = get_sql_weights()

        if self.fields is not None:
            search_fields = self.queryset.model.get_searchable_search_fields()
            self.search_fields = {
                field_lookup: self.get_search_field(field_lookup, fields=search_fields)
                for field_lookup in self.fields
            }

    def get_search_field(self, field_lookup, fields=None):
        if fields is None:
            fields = self.search_fields

        if LOOKUP_SEP in field_lookup:
            field_lookup, sub_field_name = field_lookup.split(LOOKUP_SEP, 1)
        else:
            sub_field_name = None

        for field in fields:
            if isinstance(field, SearchField) and field.field_name == field_lookup:
                return field

            # Note: Searching on a specific related field using
            # `.search(fields=…)` is not yet supported by Wagtail.
            # This method anticipates by already implementing it.
            if isinstance(field, RelatedFields) and field.field_name == field_lookup:
                return self.get_search_field(sub_field_name, field.fields)

    def build_tsquery_content(self, query, invert=False):
        if isinstance(query, PlainText):
            terms = query.query_string.split()
            if not terms:
                return None

            last_term = terms.pop()

            lexemes = Lexeme(last_term, invert=invert, prefix=self.LAST_TERM_IS_PREFIX)
            for term in terms:
                new_lexeme = Lexeme(term, invert=invert)

                if query.operator == 'and':
                    lexemes &= new_lexeme
                else:
                    lexemes |= new_lexeme

            return lexemes

        elif isinstance(query, Boost):
            # Not supported
            return self.build_tsquery_content(query.subquery, invert=invert)

        elif isinstance(query, Not):
            return self.build_tsquery_content(query.subquery, invert=not invert)

        elif isinstance(query, (And, Or)):
            # If this part of the query is inverted, we swap the operator and
            # pass down the inversion state to the child queries.
            # This works thanks to De Morgan's law.
            #
            # For example, the following query:
            #
            #   Not(And(Term("A"), Term("B")))
            #
            # Is equivalent to:
            #
            #   Or(Not(Term("A")), Not(Term("B")))
            #
            # It's simpler to code it this way as we only need to store the
            # invert status of the terms rather than all the operators.

            subquery_lexemes = [
                self.build_tsquery_content(subquery, invert=invert)
                for subquery in query.subqueries
            ]

            is_and = isinstance(query, And)

            if invert:
                is_and = not is_and

            if is_and:
                return reduce(lambda a, b: a & b, subquery_lexemes)
            else:
                return reduce(lambda a, b: a | b, subquery_lexemes)

        raise NotImplementedError(
            '`%s` is not supported by the PostgreSQL search backend.'
            % query.__class__.__name__)

    def build_tsquery(self, query, config=None):
        return RawSearchQuery(self.build_tsquery_content(query), config=config)

    def build_tsrank(self, vector, query, config=None, boost=1.0):
        if isinstance(query, (PlainText, Not)):
            rank_expression = SearchRank(
                vector,
                self.build_tsquery(query, config=config),
                weights=self.sql_weights
            )

            if boost != 1.0:
                rank_expression *= boost

            return rank_expression

        elif isinstance(query, Boost):
            boost *= query.boost
            return self.build_tsrank(vector, query.subquery, config=config, boost=boost)

        elif isinstance(query, And):
            return MUL(
                1 + self.build_tsrank(vector, subquery, config=config, boost=boost)
                for subquery in query.subqueries
            ) - 1

        elif isinstance(query, Or):
            return ADD(
                self.build_tsrank(vector, subquery, config=config, boost=boost)
                for subquery in query.subqueries
            ) / (len(query.subqueries) or 1)

        raise NotImplementedError(
            '`%s` is not supported by the PostgreSQL search backend.'
            % query.__class__.__name__)

    def get_index_vector(self, search_query):
        return F('index_entries__autocomplete')._combine(
            F('index_entries__body'), '||', False)

    def get_fields_vector(self, search_query):
        return ADD(
            SearchVector(
                field_lookup,
                config=search_query.config,
                weight=get_weight(search_field.boost)
            )
            for field_lookup, search_field in self.search_fields.items()
        )

    def get_search_vector(self, search_query):
        if self.fields is None:
            return self.get_index_vector(search_query)

        else:
            return self.get_fields_vector(search_query)

    def search(self, config, start, stop, score_field=None):
        # TODO: Handle MatchAll nested inside other search query classes.
        if isinstance(self.query, MatchAll):
            return self.queryset[start:stop]

        search_query = self.build_tsquery(self.query, config=config)
        vector = self.get_search_vector(search_query)
        rank_expression = self.build_tsrank(vector, self.query, config=config)
        queryset = self.queryset.annotate(_vector_=vector).filter(_vector_=search_query)

        if self.order_by_relevance:
            queryset = queryset.order_by(rank_expression.desc(), '-pk')

        elif not queryset.query.order_by:
            # Adds a default ordering to avoid issue #3729.
            queryset = queryset.order_by('-pk')
            rank_expression = F('pk')

        if score_field is not None:
            queryset = queryset.annotate(**{score_field: rank_expression})

        return queryset[start:stop]

    def _process_lookup(self, field, lookup, value):
        lhs = field.get_attname(self.queryset.model) + '__' + lookup
        return Q(**{lhs: value})

    def _connect_filters(self, filters, connector, negated):
        if connector == 'AND':
            q = Q(*filters)

        elif connector == 'OR':
            q = OR([Q(fil) for fil in filters])

        else:
            return

        if negated:
            q = ~q

        return q


class PostgresAutocompleteQueryCompiler(PostgresSearchQueryCompiler):
    LAST_TERM_IS_PREFIX = True

    def get_index_vector(self, search_query):
        return F('index_entries__autocomplete')

    def get_fields_vector(self, search_query):
        return ADD(
            SearchVector(
                field_lookup,
                config=search_query.config,
                weight=get_weight(search_field.boost)
            )
            for field_lookup, search_field in self.search_fields.items()
            if search_field.partial_match
        )


class PostgresSearchResults(BaseSearchResults):
    def _do_search(self):
        return list(self.query_compiler.search(self.backend.config,
                                               self.start, self.stop,
                                               score_field=self._score_field))

    def _do_count(self):
        return self.query_compiler.search(
            self.backend.config, None, None,
            score_field=self._score_field).count()

    supports_facet = True

    def facet(self, field_name):
        # Get field
        field = self.query_compiler._get_filterable_field(field_name)
        if field is None:
            raise FilterFieldError(
                'Cannot facet search results with field "' + field_name + '". Please add index.FilterField(\''
                + field_name + '\') to ' + self.query_compiler.queryset.model.__name__ + '.search_fields.',
                field_name=field_name
            )

        query = self.query_compiler.search(self.backend.config, None, None)
        results = query.values(field_name).annotate(count=Count('pk')).order_by('-count')

        return OrderedDict([
            (result[field_name], result['count'])
            for result in results
        ])


class PostgresSearchRebuilder:
    def __init__(self, index):
        self.index = index

    def start(self):
        self.index.delete_stale_entries()
        return self.index

    def finish(self):
        pass


class PostgresSearchAtomicRebuilder(PostgresSearchRebuilder):
    def __init__(self, index):
        super().__init__(index)
        self.transaction = transaction.atomic(using=index.db_alias)
        self.transaction_opened = False

    def start(self):
        self.transaction.__enter__()
        self.transaction_opened = True
        return super().start()

    def finish(self):
        self.transaction.__exit__(None, None, None)
        self.transaction_opened = False

    def __del__(self):
        # TODO: Implement a cleaner way to close the connection on failure.
        if self.transaction_opened:
            self.transaction.needs_rollback = True
            self.finish()


class PostgresSearchBackend(BaseSearchBackend):
    query_compiler_class = PostgresSearchQueryCompiler
    autocomplete_query_compiler_class = PostgresAutocompleteQueryCompiler
    results_class = PostgresSearchResults
    rebuilder_class = PostgresSearchRebuilder
    atomic_rebuilder_class = PostgresSearchAtomicRebuilder

    def __init__(self, params):
        super().__init__(params)
        self.index_name = params.get('INDEX', 'default')
        self.config = params.get('SEARCH_CONFIG')
        if params.get('ATOMIC_REBUILD', False):
            self.rebuilder_class = self.atomic_rebuilder_class

    def get_index_for_model(self, model, db_alias=None):
        return Index(self, db_alias)

    def get_index_for_object(self, obj):
        return self.get_index_for_model(obj._meta.model, obj._state.db)

    def reset_index(self):
        for connection in get_postgresql_connections():
            IndexEntry._default_manager.using(connection.alias).delete()

    def add_type(self, model):
        pass  # Not needed.

    def refresh_index(self):
        pass  # Not needed.

    def add(self, obj):
        self.get_index_for_object(obj).add_item(obj)

    def add_bulk(self, model, obj_list):
        if obj_list:
            self.get_index_for_object(obj_list[0]).add_items(model, obj_list)

    def delete(self, obj):
        self.get_index_for_object(obj).delete_item(obj)


SearchBackend = PostgresSearchBackend
