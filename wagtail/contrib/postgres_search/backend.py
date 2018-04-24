from warnings import warn

from django.contrib.postgres.search import SearchQuery as PostgresSearchQuery
from django.contrib.postgres.search import SearchRank, SearchVector
from django.db import DEFAULT_DB_ALIAS, NotSupportedError, connections, transaction
from django.db.models import F, Manager, Q, TextField, Value
from django.db.models.constants import LOOKUP_SEP
from django.db.models.functions import Cast
from django.utils.encoding import force_text

from wagtail.search.backends.base import (
    BaseSearchBackend, BaseSearchQueryCompiler, BaseSearchResults)
from wagtail.search.index import RelatedFields, SearchField
from wagtail.search.query import And, MatchAll, Not, Or, SearchQueryShortcut, Term
from wagtail.search.utils import ADD, AND, OR

from .models import IndexEntry
from .utils import (
    WEIGHTS_VALUES, get_ancestors_content_types_pks, get_content_type_pk,
    get_descendants_content_types_pks, get_postgresql_connections, get_weight, unidecode)


# TODO: Add autocomplete.


class Index:
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
        self.index_entries = IndexEntry._default_manager.using(self.db_alias)
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
            self.index_entries.filter(content_type_id__in=content_type_ids)
            .exclude(object_id__in=existing_pks))
        stale_entries.delete()

    def prepare_value(self, value):
        if isinstance(value, str):
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
                ADD([SearchVector(Value(text), weight=weight, config=config)
                     for text, weight in obj._body_])
                if obj._body_ else SearchVector(Value('')))
            ids_and_objs[obj._object_id] = obj
        index_entries_for_ct = self.index_entries.filter(
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
        self.index_entries.bulk_create(to_be_created)

    def add_items(self, model, objs):
        content_type_pk = get_content_type_pk(model)
        config = self.backend.get_config()
        for obj in objs:
            obj._object_id = force_text(obj.pk)
            obj._body_ = self.prepare_body(obj)

        # Removes index entries of an ancestor model in case the descendant
        # model instance was created since.
        self.index_entries.filter(
            content_type_id__in=get_ancestors_content_types_pks(model)
        ).filter(object_id__in=[obj._object_id for obj in objs]).delete()

        connection = connections[self.db_alias]
        if connection.pg_version >= 90500:  # PostgreSQL >= 9.5
            self.add_items_upsert(connection, content_type_pk, objs, config)
        else:
            self.add_items_update_then_create(content_type_pk, objs, config)

    def delete_item(self, item):
        item.index_entries.using(self.db_alias).delete()

    def __str__(self):
        return self.name


class PostgresSearchQueryCompiler(BaseSearchQueryCompiler):
    DEFAULT_OPERATOR = 'and'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_fields = self.queryset.model.get_searchable_search_fields()

    def build_database_query(self, query=None, config=None):
        if query is None:
            query = self.query

        if isinstance(query, SearchQueryShortcut):
            return self.build_database_query(query.get_equivalent(), config)
        if isinstance(query, Term):
            # TODO: Find a way to use the term boosting.
            if query.boost != 1:
                warn('PostgreSQL search backend '
                     'does not support term boosting for now.')
            return PostgresSearchQuery(unidecode(query.term), config=config)
        if isinstance(query, Not):
            return ~self.build_database_query(query.subquery, config)
        if isinstance(query, And):
            return AND(self.build_database_query(subquery, config)
                       for subquery in query.subqueries)
        if isinstance(query, Or):
            return OR(self.build_database_query(subquery, config)
                      for subquery in query.subqueries)
        raise NotImplementedError(
            '`%s` is not supported by the PostgreSQL search backend.'
            % self.query.__class__.__name__)

    def get_boost(self, field_name, fields=None):
        if fields is None:
            fields = self.search_fields
        if LOOKUP_SEP in field_name:
            field_name, sub_field_name = field_name.split(LOOKUP_SEP, 1)
        else:
            sub_field_name = None
        for field in fields:
            if isinstance(field, SearchField) \
                    and field.field_name == field_name:
                # Note: Searching on a specific related field using
                # `.search(fields=…)` is not yet supported by Wagtail.
                # This method anticipates by already implementing it.
                if isinstance(field, RelatedFields):
                    return self.get_boost(sub_field_name, field.fields)
                return field.boost

    def search(self, config, start, stop):
        # TODO: Handle MatchAll nested inside other search query classes.
        if isinstance(self.query, MatchAll):
            return self.queryset[start:stop]

        search_query = self.build_database_query(config=config)
        queryset = self.queryset
        query = queryset.query
        if self.fields is None:
            vector = F('index_entries__body_search')
        else:
            vector = ADD(
                SearchVector(field, config=search_query.config,
                             weight=get_weight(self.get_boost(field)))
                for field in self.fields)
        vector = vector.resolve_expression(query)
        search_query = search_query.resolve_expression(query)
        lookup = IndexEntry._meta.get_field('body_search').get_lookup('exact')(
            vector, search_query)
        query.where.add(lookup, 'AND')
        if self.order_by_relevance:
            # Due to a Django bug, arrays are not automatically converted here.
            converted_weights = '{' + ','.join(map(str, WEIGHTS_VALUES)) + '}'
            queryset = queryset.order_by(SearchRank(vector, search_query,
                                                    weights=converted_weights).desc(),
                                         '-pk')
        elif not queryset.query.order_by:
            # Adds a default ordering to avoid issue #3729.
            queryset = queryset.order_by('-pk')
        return queryset[start:stop]

    def _process_lookup(self, field, lookup, value):
        return Q(**{field.get_attname(self.queryset.model) +
                    '__' + lookup: value})

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


class PostgresSearchResults(BaseSearchResults):
    def _do_search(self):
        return list(self.query_compiler.search(self.backend.get_config(),
                                               self.start, self.stop))

    def _do_count(self):
        return self.query_compiler.search(self.backend.get_config(), None, None).count()


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
    results_class = PostgresSearchResults
    rebuilder_class = PostgresSearchRebuilder
    atomic_rebuilder_class = PostgresSearchAtomicRebuilder

    def __init__(self, params):
        super().__init__(params)
        self.params = params
        if params.get('ATOMIC_REBUILD', False):
            self.rebuilder_class = self.atomic_rebuilder_class

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
        self.get_index_for_object(obj).delete_item(obj)


SearchBackend = PostgresSearchBackend
