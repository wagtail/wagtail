# coding: utf-8

from __future__ import absolute_import, unicode_literals

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import DEFAULT_DB_ALIAS, NotSupportedError, connections, transaction
from django.db.models import F, Manager, Q, TextField, Value
from django.db.models.constants import LOOKUP_SEP
from django.db.models.functions import Cast
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.six import string_types

from wagtail.wagtailsearch.backends.base import (
    BaseSearchBackend, BaseSearchQuery, BaseSearchResults)
from wagtail.wagtailsearch.index import RelatedFields, SearchField

from .models import IndexEntry, SearchAutocomplete
from .utils import (
    ADD, AND, OR, get_content_type_pk, get_descendants_content_types_pks,
    get_postgresql_connections, get_sql_weights, get_weight, keyword_split, unidecode)


@python_2_unicode_compatible
class Index(object):
    def __init__(self, backend, model, db_alias=None):
        self.backend = backend
        self.model = model
        if db_alias is None:
            db_alias = DEFAULT_DB_ALIAS
        if connections[db_alias].vendor != 'postgresql':
            raise NotSupportedError(
                'You must select a PostgreSQL database '
                'to use PostgreSQL search.')
        self.db_alias = db_alias
        self.name = model._meta.label
        self.search_fields = self.model.get_search_fields()

    def add_model(self, model):
        pass

    def refresh(self):
        pass

    def delete_stale_entries(self):
        if self.model._meta.parents:
            # We don’t need to delete stale entries for non-root models,
            # since we already delete them by deleting roots.
            return
        existing_pks = (self.model._default_manager.using(self.db_alias)
                        .annotate(object_id=Cast('pk', TextField()))
                        .values('object_id'))
        content_type_ids = get_descendants_content_types_pks(self.model)
        stale_entries = (
            IndexEntry._default_manager.using(self.db_alias)
            .filter(content_type_id__in=content_type_ids)
            .exclude(object_id__in=existing_pks))
        stale_entries.delete()

    def prepare_value(self, value):
        if isinstance(value, string_types):
            return value
        if isinstance(value, list):
            return ', '.join(self.prepare_value(item) for item in value)
        if isinstance(value, dict):
            return ', '.join(self.prepare_value(item)
                             for item in value.values())
        return force_text(value)

    def prepare_field(self, obj, field):
        if isinstance(field, SearchField):
            yield (unidecode(self.prepare_value(field.get_value(obj))),
                   get_weight(field.boost))
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
                    for value in self.prepare_field(sub_obj, sub_field):
                        yield value

    def prepare_obj(self, obj):
        obj._object_id_ = force_text(obj.pk)
        obj._autocomplete_ = []
        obj._body_ = []
        for field in self.search_fields:
            is_autocomplete = (isinstance(field, SearchField) and
                               field.partial_match)
            for value_and_boost in self.prepare_field(obj, field):
                if is_autocomplete:
                    obj._autocomplete_.append(value_and_boost)
                else:
                    obj._body_.append(value_and_boost)

    def add_item(self, obj):
        self.add_items(self.model, [obj])

    def add_items_upsert(self, connection, content_type_pk, objs, config):
        autocomplete_sql = []
        body_sql = []
        data_params = []
        sql_template = ('to_tsvector(%s)' if config is None
                        else "to_tsvector('%s', %%s)" % config)
        sql_template = 'setweight(%s, %%s)' % sql_template
        for obj in objs:
            data_params.extend((content_type_pk, obj._object_id_))
            if obj._autocomplete_:
                autocomplete_sql.append('||'.join(sql_template
                                                  for _ in obj._autocomplete_))
                data_params.extend([v for t in obj._autocomplete_ for v in t])
            else:
                autocomplete_sql.append("''::tsvector")
            if obj._body_:
                body_sql.append('||'.join(sql_template for _ in obj._body_))
                data_params.extend([v for t in obj._body_ for v in t])
            else:
                body_sql.append("''::tsvector")
        data_sql = ', '.join(['(%%s, %%s, %s, %s)' % (a, b)
                              for a, b in zip(autocomplete_sql, body_sql)])
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO %s
                (content_type_id, object_id, autocomplete, body)
                (VALUES %s)
                ON CONFLICT (content_type_id, object_id)
                DO UPDATE SET autocomplete = EXCLUDED.autocomplete,
                              body = EXCLUDED.body
                """ % (IndexEntry._meta.db_table, data_sql), data_params)

    def add_items_update_then_create(self, content_type_pk, objs, config):
        ids_and_objs = {}
        for obj in objs:
            obj._autocomplete_ = (
                ADD([SearchVector(Value(text), weight=weight, config=config)
                     for text, weight in obj._autocomplete_])
                if obj._autocomplete_ else SearchVector(Value('')))
            obj._body_ = (
                ADD([SearchVector(Value(text), weight=weight, config=config)
                     for text, weight in obj._body_])
                if obj._body_ else SearchVector(Value('')))
            ids_and_objs[obj._object_id_] = obj
        index_entries = IndexEntry._default_manager.using(self.db_alias)
        index_entries_for_ct = index_entries.filter(
            content_type_id=content_type_pk)
        indexed_ids = frozenset(
            index_entries_for_ct.filter(object_id__in=ids_and_objs)
            .values_list('object_id', flat=True))
        for indexed_id in indexed_ids:
            obj = ids_and_objs[indexed_id]
            index_entries_for_ct.filter(object_id=obj._object_id_) \
                .update(autocomplete=obj._autocomplete_, body=obj._body_)
        to_be_created = []
        for object_id in ids_and_objs:
            if object_id not in indexed_ids:
                obj = ids_and_objs[object_id]
                to_be_created.append(IndexEntry(
                    content_type_id=content_type_pk,
                    object_id=object_id,
                    autocomplete=obj._autocomplete_, body=obj._body_))
        index_entries.bulk_create(to_be_created)

    def add_items(self, model, objs):
        content_type_pk = get_content_type_pk(model)
        config = self.backend.get_config()
        for obj in objs:
            self.prepare_obj(obj)
        connection = connections[self.db_alias]
        if connection.pg_version >= 90500:  # PostgreSQL >= 9.5
            self.add_items_upsert(connection, content_type_pk, objs, config)
        else:
            self.add_items_update_then_create(content_type_pk, objs, config)

    def __str__(self):
        return self.name


class PostgresSearchQuery(BaseSearchQuery):
    DEFAULT_OPERATOR = 'and'
    expr_class = SearchQuery

    def __init__(self, *args, **kwargs):
        super(PostgresSearchQuery, self).__init__(*args, **kwargs)
        self.search_fields = self.queryset.model.get_search_fields()
        self.sql_weights = get_sql_weights()

    def get_search_query(self, config):
        combine = OR if self.operator == 'or' else AND
        search_terms = keyword_split(unidecode(self.query_string))
        if not search_terms:
            return self.expr_class('')
        return combine(self.expr_class(q, config=config) for q in search_terms)

    def get_boost(self, field_name, fields=None):
        if fields is None:
            fields = self.search_fields
        if LOOKUP_SEP in field_name:
            field_name, sub_field_name = field_name.split(LOOKUP_SEP, 1)
        else:
            sub_field_name = None
        for field in fields:
            if field.field_name == field_name:
                # Note: Searching on a specific related field using
                # `.search(fields=…)` is not yet supported by Wagtail.
                # This method anticipates by already implementing it.
                if isinstance(field, RelatedFields):
                    return self.get_boost(sub_field_name, field.fields)
                return field.boost

    def filter_queryset(self, queryset, search_query):
        return queryset.filter(Q(index_entries__autocomplete=search_query) |
                               Q(index_entries__body=search_query))

    def build_rank_expression(self, vector, search_query):
        return SearchRank(vector, search_query,
                          weights=self.sql_weights)

    def get_index_rank_expression(self, search_query):
        return (self.build_rank_expression(F('index_entries__autocomplete'),
                                           search_query) +
                self.build_rank_expression(F('index_entries__body'),
                                           search_query))

    def search_in_index(self, queryset, search_query):
        queryset = self.filter_queryset(queryset, search_query)
        return queryset, self.get_index_rank_expression(search_query)

    def search_in_fields(self, queryset, search_query):
        query = queryset.query
        vector = ADD(
            SearchVector(field, config=search_query.config,
                         weight=get_weight(self.get_boost(field)))
            for field in self.fields)
        vector = vector.resolve_expression(query)
        search_query = search_query.resolve_expression(query)
        lookup = IndexEntry._meta.get_field('body').get_lookup('exact')(
            vector, search_query)
        query.where.add(lookup, 'AND')
        return queryset, self.build_rank_expression(vector, search_query)

    def search(self, config, start, stop):
        if self.query_string is None:
            return self.queryset[start:stop]
        search_query = self.get_search_query(config=config)
        queryset, rank_expression = (
            self.search_in_index(self.queryset, search_query)
            if self.fields is None
            else self.search_in_fields(self.queryset, search_query))
        if self.order_by_relevance:
            queryset = queryset.order_by(rank_expression.desc(), '-pk')
        elif not queryset.query.order_by:
            # Adds a default ordering to avoid issue #3729.
            queryset = queryset.order_by('-pk')
        return queryset[start:stop]


class PostgresAutocompleteQuery(PostgresSearchQuery):
    expr_class = SearchAutocomplete

    def filter_queryset(self, queryset, search_query):
        return queryset.filter(index_entries__autocomplete=search_query)

    def get_index_rank_expression(self, search_query):
        return self.build_rank_expression(F('index_entries__autocomplete'),
                                          search_query)


class PostgresSearchResults(BaseSearchResults):
    def _do_search(self):
        return list(self.query.search(self.backend.get_config(),
                                      self.start, self.stop))

    def _do_count(self):
        return self.query.search(self.backend.get_config(), None, None).count()


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
        super(PostgresSearchAtomicRebuilder, self).__init__(index)
        self.transaction = transaction.atomic(using=index.db_alias)
        self.transaction_opened = False

    def start(self):
        self.transaction.__enter__()
        self.transaction_opened = True
        return super(PostgresSearchAtomicRebuilder, self).start()

    def finish(self):
        self.transaction.__exit__(None, None, None)
        self.transaction_opened = False

    def __del__(self):
        # TODO: Implement a cleaner way to close the connection on failure.
        if self.transaction_opened:
            self.transaction.needs_rollback = True
            self.finish()


class PostgresSearchBackend(BaseSearchBackend):
    query_class = PostgresSearchQuery
    autocomplete_query_class = PostgresAutocompleteQuery
    results_class = PostgresSearchResults
    rebuilder_class = PostgresSearchRebuilder
    atomic_rebuilder_class = PostgresSearchAtomicRebuilder

    def __init__(self, params):
        super(PostgresSearchBackend, self).__init__(params)
        self.params = params
        if params.get('ATOMIC_REBUILD', False):
            self.rebuilder_class = self.atomic_rebuilder_class
        IndexEntry.add_generic_relations()

    def get_config(self):
        return self.params.get('SEARCH_CONFIG')

    def get_index_for_model(self, model, db_alias=None):
        return Index(self, model, db_alias)

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
        obj.index_entries.all().delete()

    def autocomplete(self, query_string, model_or_queryset, fields=None,
                     filters=None, prefetch_related=None, operator=None,
                     order_by_relevance=True):
        args, kwargs = self.get_search_params(
            query_string, model_or_queryset, fields=fields, filters=filters,
            prefetch_related=prefetch_related, operator=operator,
            order_by_relevance=order_by_relevance)
        return self.results_class(
            self, self.autocomplete_query_class(*args, **kwargs))


SearchBackend = PostgresSearchBackend
