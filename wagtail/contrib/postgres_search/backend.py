# coding: utf-8

from __future__ import absolute_import, unicode_literals

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import DEFAULT_DB_ALIAS, NotSupportedError, connections, transaction
from django.db.models import F, Manager, TextField, Value
from django.db.models.constants import LOOKUP_SEP
from django.db.models.functions import Cast
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.six import string_types

from wagtail.wagtailsearch.backends.base import (
    BaseSearchBackend, BaseSearchQuery, BaseSearchResults)
from wagtail.wagtailsearch.index import RelatedFields, SearchField

from .models import IndexEntry
from .utils import (
    ADD, AND, OR, WEIGHTS_VALUES, get_content_types_pks, get_postgresql_connections, get_weight,
    keyword_split, unidecode)


# TODO: Add autocomplete.


def get_db_alias(queryset):
    return queryset._db or DEFAULT_DB_ALIAS


def get_sql(queryset):
    return queryset.query.get_compiler(get_db_alias(queryset)).as_sql()


def get_pk_column(model):
    return model._meta.pk.get_attname_column()[1]


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
        stale_entries = (IndexEntry._default_manager.using(self.db_alias)
                         .for_models(self.model)
                         .exclude(object_id__in=existing_pks))
        stale_entries.delete()

    def get_config(self):
        return self.backend.params.get('SEARCH_CONFIG')

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

    def prepare_body(self, obj):
        return [(value, boost) for field in self.search_fields
                for value, boost in self.prepare_field(obj, field)]

    def add_item(self, obj):
        self.add_items(self.model, [obj])

    def add_items_upsert(self, connection, content_type_pk, objs, config):
        vectors_sql = []
        data_params = []
        sql_template = ('to_tsvector(%s)' if config is None
                        else "to_tsvector('%s', %%s)" % config)
        sql_template = 'setweight(%s, %%s)' % sql_template
        for obj in objs:
            data_params.extend((content_type_pk, obj._object_id))
            if obj._body_:
                vectors_sql.append('||'.join(sql_template for _ in obj._body_))
                data_params.extend([v for t in obj._body_ for v in t])
            else:
                vectors_sql.append("''::tsvector")
        data_sql = ', '.join(['(%%s, %%s, %s)' % s for s in vectors_sql])
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO %s(content_type_id, object_id, body_search)
                (VALUES %s)
                ON CONFLICT (content_type_id, object_id)
                DO UPDATE SET body_search = EXCLUDED.body_search
                """ % (IndexEntry._meta.db_table, data_sql), data_params)

    def add_items_update_then_create(self, content_type_pk, objs, config):
        ids_and_objs = {}
        for obj in objs:
            obj._search_vector = (
                ADD([
                    SearchVector(Value(text), weight=weight, config=config)
                    for text, weight in obj._body_])
                if obj._body_ else SearchVector(Value('')))
            ids_and_objs[obj._object_id] = obj
        index_entries = IndexEntry._default_manager.using(self.db_alias)
        index_entries_for_ct = index_entries.filter(
            content_type_id=content_type_pk)
        indexed_ids = frozenset(
            index_entries_for_ct.filter(object_id__in=ids_and_objs)
            .values_list('object_id', flat=True))
        for indexed_id in indexed_ids:
            obj = ids_and_objs[indexed_id]
            index_entries_for_ct.filter(object_id=obj._object_id) \
                .update(body_search=obj._search_vector)
        to_be_created = []
        for object_id in ids_and_objs:
            if object_id not in indexed_ids:
                to_be_created.append(IndexEntry(
                    content_type_id=content_type_pk,
                    object_id=object_id,
                    body_search=ids_and_objs[object_id]._search_vector,
                ))
        index_entries.bulk_create(to_be_created)

    def add_items(self, model, objs):
        content_type_pk = get_content_types_pks((model,), self.db_alias)[0]
        config = self.get_config()
        for obj in objs:
            obj._object_id = force_text(obj.pk)
            obj._body_ = self.prepare_body(obj)
        connection = connections[self.db_alias]
        if connection.pg_version >= 90500:  # PostgreSQL >= 9.5
            self.add_items_upsert(connection, content_type_pk, objs, config)
        else:
            self.add_items_update_then_create(content_type_pk, objs, config)

    def __str__(self):
        return self.name


class PostgresSearchQuery(BaseSearchQuery):
    DEFAULT_OPERATOR = 'and'

    def __init__(self, *args, **kwargs):
        super(PostgresSearchQuery, self).__init__(*args, **kwargs)
        self.search_fields = self.queryset.model.get_search_fields()

    def get_search_query(self, config):
        combine = OR if self.operator == 'or' else AND
        search_terms = keyword_split(unidecode(self.query_string))
        if not search_terms:
            return SearchQuery('')
        return combine(SearchQuery(q, config=config) for q in search_terms)

    def get_base_queryset(self):
        # Removes order for performance’s sake.
        return self.queryset.order_by()

    def get_in_index_queryset(self, queryset, search_query):
        return (IndexEntry._default_manager.using(get_db_alias(queryset))
                .for_models(queryset.model).filter(body_search=search_query))

    def get_in_index_count(self, queryset, search_query):
        index_sql, index_params = get_sql(
            self.get_in_index_queryset(queryset, search_query).pks())
        model_sql, model_params = get_sql(queryset)
        sql = """
            SELECT COUNT(*)
            FROM (%s) AS index_entry
            INNER JOIN (%s) AS obj ON obj."%s" = index_entry.typed_pk;
            """ % (index_sql, model_sql, get_pk_column(queryset.model))
        with connections[get_db_alias(queryset)].cursor() as cursor:
            cursor.execute(sql, index_params + model_params)
            return cursor.fetchone()[0]

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

    def get_in_fields_queryset(self, queryset, search_query):
        if not self.fields:
            return queryset.none()
        return (
            queryset.annotate(
                _search_=ADD(
                    SearchVector(field, config=search_query.config,
                                 weight=get_weight(self.get_boost(field)))
                    for field in self.fields))
            .filter(_search_=search_query))

    def search_count(self, config):
        queryset = self.get_base_queryset()
        search_query = self.get_search_query(config=config)
        if self.fields is None:
            return self.get_in_index_count(queryset, search_query)
        return self.get_in_fields_queryset(queryset, search_query).count()

    def search_in_index(self, queryset, search_query, start, stop):
        index_entries = self.get_in_index_queryset(queryset, search_query)
        if self.order_by_relevance:
            index_entries = index_entries.rank(search_query)
        index_sql, index_params = get_sql(
            index_entries.annotate_typed_pk()
            .values('typed_pk', 'rank')
        )
        model_sql, model_params = get_sql(queryset)
        model = queryset.model
        sql = """
            SELECT obj.*
            FROM (%s) AS index_entry
            INNER JOIN (%s) AS obj ON obj."%s" = index_entry.typed_pk
            ORDER BY index_entry.rank DESC
            OFFSET %%s LIMIT %%s;
            """ % (index_sql, model_sql, get_pk_column(model))
        limits = (start, None if stop is None else stop - start)
        return model._default_manager.using(get_db_alias(queryset)).raw(
            sql, index_params + model_params + limits)

    def search_in_fields(self, queryset, search_query, start, stop):
        return (self.get_in_fields_queryset(queryset, search_query)
                .annotate(_rank_=SearchRank(F('_search_'), search_query,
                                            weights=WEIGHTS_VALUES))
                .order_by('-_rank_'))[start:stop]

    def search(self, config, start, stop):
        queryset = self.get_base_queryset()
        if self.query_string is None:
            return queryset[start:stop]
        search_query = self.get_search_query(config=config)
        if self.fields is None:
            return self.search_in_index(queryset, search_query, start, stop)
        return self.search_in_fields(queryset, search_query, start, stop)


class PostgresSearchResult(BaseSearchResults):
    def get_config(self):
        queryset = self.query.queryset
        return self.backend.get_index_for_model(
            queryset.model, queryset._db).get_config()

    def _do_search(self):
        return list(self.query.search(self.get_config(),
                                      self.start, self.stop))

    def _do_count(self):
        return self.query.search_count(self.get_config())


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
    results_class = PostgresSearchResult
    rebuilder_class = PostgresSearchRebuilder
    atomic_rebuilder_class = PostgresSearchAtomicRebuilder

    def __init__(self, params):
        super(PostgresSearchBackend, self).__init__(params)
        self.params = params
        if params.get('ATOMIC_REBUILD', False):
            self.rebuilder_class = self.atomic_rebuilder_class

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
        IndexEntry._default_manager.for_object(obj).delete()


SearchBackend = PostgresSearchBackend
