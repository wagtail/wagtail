from collections import OrderedDict
from functools import reduce

from django.db import DEFAULT_DB_ALIAS, NotSupportedError, connections, transaction
from django.db.models import Avg, Count, F, Manager, Q, TextField
from django.db.models.constants import LOOKUP_SEP
from django.db.models.functions import Cast, Length
from django.db.utils import OperationalError
from django.utils.encoding import force_str
from django.utils.functional import cached_property

from ....index import AutocompleteField, RelatedFields, SearchField, get_indexed_models
from ....models import IndexEntry, SQLiteFTSIndexEntry
from ....query import And, MatchAll, Not, Or, Phrase, PlainText
from ....utils import ADD, MUL, OR, get_content_type_pk, get_descendants_content_types_pks
from ...base import BaseSearchBackend, BaseSearchQueryCompiler, BaseSearchResults, FilterFieldError
from .query import BM25, AndNot, Lexeme, MatchExpression, SearchQueryExpression, normalize


class ObjectIndexer:
    """
    Responsible for extracting data from an object to be inserted into the index.
    """

    def __init__(self, obj, backend):
        self.obj = obj
        self.search_fields = obj.get_search_fields()
        self.config = backend.config

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
            yield (field,
                   self.prepare_value(field.get_value(obj)))

        elif isinstance(field, AutocompleteField):
            yield (field, self.prepare_value(field.get_value(obj)))

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

    @cached_property
    def id(self):
        """
        Returns the value to use as the ID of the record in the index
        """
        return force_str(self.obj.pk)

    @cached_property
    def title(self):
        """
        Returns all values to index as "title". This is the value of all SearchFields that have the field_name 'title'
        """
        texts = []
        for field in self.search_fields:
            for current_field, value in self.prepare_field(self.obj, field):
                if isinstance(current_field, SearchField) and current_field.field_name == 'title':
                    texts.append((value))

        return ' '.join(texts)

    @cached_property
    def body(self):
        """
        Returns all values to index as "body". This is the value of all SearchFields excluding the title
        """
        texts = []
        for field in self.search_fields:
            for current_field, value in self.prepare_field(self.obj, field):
                if isinstance(current_field, SearchField) and not current_field.field_name == 'title':
                    texts.append((value))

        return ' '.join(texts)

    @cached_property
    def autocomplete(self):
        """
        Returns all values to index as "autocomplete". This is the value of all AutocompleteFields
        """
        texts = []
        for field in self.search_fields:
            for current_field, value in self.prepare_field(self.obj, field):
                if isinstance(current_field, AutocompleteField):
                    texts.append((value))

        return ' '.join(texts)

    def as_vector(self, texts, for_autocomplete=False):
        """
        Converts an array of strings into a SearchVector that can be indexed.
        """
        texts = [(text.strip(), weight) for text, weight in texts]
        texts = [(text, weight) for text, weight in texts if text]

        return ' '.join(texts)


class Index:
    def __init__(self, backend, db_alias=None):
        self.backend = backend
        self.name = self.backend.index_name
        self.db_alias = DEFAULT_DB_ALIAS if db_alias is None else db_alias
        self.connection = connections[self.db_alias]
        if self.connection.vendor != 'sqlite':
            raise NotSupportedError(
                'You must select a SQLite database '
                'to use the SQLite search backend.')

        self.entries = IndexEntry._default_manager.using(self.db_alias)

    def add_model(self, model):
        pass

    def refresh(self):
        pass

    def _refresh_title_norms(self, full=False):
        """
        Refreshes the value of the title_norm field.

        This needs to be set to 'lavg/ld' where:
         - lavg is the average length of titles in all documents (also in terms)
         - ld is the length of the title field in this document (in terms)
        """

        lavg = self.entries.annotate(title_length=Length('title')).filter(title_length__gt=0).aggregate(Avg('title_length'))['title_length__avg']

        if full:
            # Update the whole table
            # This is the most accurate option but requires a full table rewrite
            # so we can't do it too often as it could lead to locking issues.
            entries = self.entries

        else:
            # Only update entries where title_norm is 1.0
            # This is the default value set on new entries.
            # It's possible that other entries could have this exact value but there shouldn't be too many of those
            entries = self.entries.filter(title_norm=1.0)

        entries.annotate(title_length=Length('title')).filter(title_length__gt=0).update(title_norm=lavg / F('title_length'))

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

    def add_items_update_then_create(self, content_type_pk, indexers):
        ids_and_data = {}
        for indexer in indexers:
            ids_and_data[indexer.id] = (indexer.title, indexer.autocomplete, indexer.body)

        index_entries_for_ct = self.entries.filter(content_type_id=content_type_pk)
        indexed_ids = frozenset(
            index_entries_for_ct.filter(object_id__in=ids_and_data.keys()).values_list('object_id', flat=True)
        )
        for indexed_id in indexed_ids:
            title, autocomplete, body = ids_and_data[indexed_id]
            index_entries_for_ct.filter(object_id=indexed_id).update(title=title, autocomplete=autocomplete, body=body)

        to_be_created = []
        for object_id in ids_and_data.keys():
            if object_id not in indexed_ids:
                title, autocomplete, body = ids_and_data[object_id]
                to_be_created.append(IndexEntry(
                    content_type_id=content_type_pk,
                    object_id=object_id,
                    title=title,
                    autocomplete=autocomplete,
                    body=body,
                ))

        self.entries.bulk_create(to_be_created)

        self._refresh_title_norms()

    def add_items(self, model, objs):
        search_fields = model.get_search_fields()
        if not search_fields:
            return

        indexers = [ObjectIndexer(obj, self.backend) for obj in objs]

        # TODO: Delete unindexed objects while dealing with proxy models.
        if indexers:
            content_type_pk = get_content_type_pk(model)

            update_method = (
                self.add_items_update_then_create)
            update_method(content_type_pk, indexers)

    def delete_item(self, item):
        item.index_entries.using(self.db_alias).delete()

    def __str__(self):
        return self.name


class SQLiteSearchRebuilder:
    def __init__(self, index):
        self.index = index

    def start(self):
        self.index.delete_stale_entries()
        return self.index

    def finish(self):
        self.index._refresh_title_norms(full=True)


class SQLiteSearchAtomicRebuilder(SQLiteSearchRebuilder):
    def __init__(self, index):
        super().__init__(index)
        self.transaction = transaction.atomic(using=index.db_alias)
        self.transaction_opened = False

    def start(self):
        self.transaction.__enter__()
        self.transaction_opened = True
        return super().start()

    def finish(self):
        self.index._refresh_title_norms(full=True)

        self.transaction.__exit__(None, None, None)
        self.transaction_opened = False

    def __del__(self):
        # TODO: Implement a cleaner way to close the connection on failure.
        if self.transaction_opened:
            self.transaction.needs_rollback = True
            self.finish()


class SQLiteSearchQueryCompiler(BaseSearchQueryCompiler):
    DEFAULT_OPERATOR = 'AND'
    LAST_TERM_IS_PREFIX = False
    TARGET_SEARCH_FIELD_TYPE = SearchField

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        local_search_fields = self.get_search_fields_for_model()

        if self.fields is None:
            # search over the fields defined on the current model
            self.search_fields = local_search_fields
        else:
            # build a search_fields set from the passed definition,
            # which may involve traversing relations
            self.search_fields = {
                field_lookup: self.get_search_field(field_lookup, fields=local_search_fields)
                for field_lookup in self.fields
            }

    def get_config(self, backend):
        return backend.config

    def get_search_fields_for_model(self):
        return self.queryset.model.get_searchable_search_fields()

    def get_search_field(self, field_lookup, fields=None):
        if fields is None:
            fields = self.search_fields

        if LOOKUP_SEP in field_lookup:
            field_lookup, sub_field_name = field_lookup.split(LOOKUP_SEP, 1)
        else:
            sub_field_name = None

        for field in fields:
            if isinstance(field, self.TARGET_SEARCH_FIELD_TYPE) and field.field_name == field_lookup:
                return field

            # Note: Searching on a specific related field using
            # `.search(fields=…)` is not yet supported by Wagtail.
            # This method anticipates by already implementing it.
            if isinstance(field, RelatedFields) and field.field_name == field_lookup:
                return self.get_search_field(sub_field_name, field.fields)

    def build_search_query_content(self, query, config=None):
        """
        Takes a SearchQuery and returns another SearchQuery object, which can be used to construct the query in SQL.
        """
        if isinstance(query, PlainText):
            terms = query.query_string.split()
            if not terms:
                return None

            last_term = terms.pop()

            lexemes = Lexeme(last_term, prefix=self.LAST_TERM_IS_PREFIX)  # Combine all terms into a single lexeme.
            for term in terms:
                new_lexeme = Lexeme(term)

                if query.operator.upper() == 'AND':
                    lexemes &= new_lexeme
                else:
                    lexemes |= new_lexeme

            return SearchQueryExpression(lexemes, config=config)

        elif isinstance(query, Phrase):
            return SearchQueryExpression(query.query_string)

        elif isinstance(query, AndNot):
            # Combine the two sub-queries into a query of the form `(first) AND NOT (second)`.
            subquery_a = self.build_search_query_content(query.subquery_a, config=config)
            subquery_b = self.build_search_query_content(query.subquery_b, config=config)
            combined_query = subquery_a._combine(subquery_b, 'NOT')
            return combined_query

        elif isinstance(query, (And, Or)):
            subquery_lexemes = [
                self.build_search_query_content(subquery, config=config)
                for subquery in query.subqueries
            ]

            is_and = isinstance(query, And)

            if is_and:
                return reduce(lambda a, b: a & b, subquery_lexemes)
            else:
                return reduce(lambda a, b: a | b, subquery_lexemes)

        raise NotImplementedError(
            '`%s` is not supported by the SQLite search backend.'
            % query.__class__.__name__)

    def build_search_query(self, query, config=None):
        if isinstance(query, MatchAll):
            return query
        if isinstance(query, Not):
            unwrapped_query = query.subquery
            built_query = Not(self.build_search_query(unwrapped_query, config=config))  # We don't take the Not operator into account.
        else:
            built_query = self.build_search_query_content(query, config=config)
        return built_query

    def build_tsrank(self, vector, query, config=None, boost=1.0):
        if isinstance(query, (Phrase, PlainText, Not)):
            rank_expression = BM25()

            if boost != 1.0:
                rank_expression *= boost

            return rank_expression

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
            '`%s` is not supported by the SQLite search backend.'
            % query.__class__.__name__)

    def get_index_vectors(self):
        return [
            (F('index_entries__title'), F('index_entries__title_norm')),
            (F('index_entries__body'), 1.0),
        ]

    def get_search_vectors(self):
        return self.get_index_vectors()

    def _build_rank_expression(self, vectors, config):

        # TODO: Come up with my own expression class that compiles down to bm25

        rank_expressions = [
            self.build_tsrank(vector, self.query, config=config) * boost
            for vector, boost in vectors
        ]

        rank_expression = rank_expressions[0]
        for other_rank_expression in rank_expressions[1:]:
            rank_expression += other_rank_expression

        return rank_expression

    def search(self, config, start, stop, score_field=None):
        normalized_query = normalize(self.query)

        if isinstance(normalized_query, MatchAll):
            return self.queryset[start:stop]

        elif isinstance(normalized_query, Not) and isinstance(normalized_query.subquery, MatchAll):
            return self.queryset.none()

        if isinstance(normalized_query, Not):
            normalized_query = normalized_query.subquery
            negated = True
        else:
            negated = False

        search_query = self.build_search_query(normalized_query, config=config)  # We build a search query here, for example: "%s MATCH '(hello AND world)'"
        vectors = self.get_search_vectors()
        rank_expression = self._build_rank_expression(vectors, config)

        combined_vector = vectors[0][0]  # We create a combined vector for the search results queryset. We start with the first vector and build from there.
        for vector, boost in vectors[1:]:
            combined_vector = combined_vector._combine(vector, ' ', False)  # We add the subsequent vectors to the combined vector.

        expr = MatchExpression(self.fields or ['title', 'body'], search_query)  # Build the FTS match expression.
        objs = SQLiteFTSIndexEntry.objects.filter(expr).select_related('index_entry')  # Perform the FTS search. We'll get entries in the SQLiteFTSIndexEntry model.

        if self.order_by_relevance:
            objs = objs.order_by(BM25().desc())
        elif not objs.query.order_by:
            # Adds a default ordering to avoid issue #3729.
            queryset = objs.order_by('-pk')
            rank_expression = F('pk')

        from django.db import connection
        from django.db.models.sql.subqueries import InsertQuery
        compiler = InsertQuery(IndexEntry).get_compiler(connection=connection)

        try:
            obj_ids = [obj.index_entry.object_id for obj in objs]  # Get the IDs of the objects that matched. They're stored in the IndexEntry model, so we need to get that first.
        except OperationalError:
            raise OperationalError('The original query was' + compiler.compile(objs.query)[0] + str(compiler.compile(objs.query)[1]))

        if not negated:
            queryset = self.queryset.filter(id__in=obj_ids)  # We need to filter the source queryset to get the objects that matched the search query.
        else:
            queryset = self.queryset.exclude(id__in=obj_ids)  # We exclude the objects that matched the search query from the source queryset, if the query is negated.

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


class SQLiteAutocompleteQueryCompiler(SQLiteSearchQueryCompiler):
    LAST_TERM_IS_PREFIX = True
    TARGET_SEARCH_FIELD_TYPE = AutocompleteField

    def get_config(self, backend):
        return backend.autocomplete_config

    def get_search_fields_for_model(self):
        return self.queryset.model.get_autocomplete_search_fields()

    def get_index_vectors(self, search_query):
        return [(F('index_entries__autocomplete'), 1.0)]

    def get_fields_vectors(self, search_query):
        raise NotImplementedError()


class SQLiteSearchResults(BaseSearchResults):
    def get_queryset(self, for_count=False):
        if for_count:
            start = None
            stop = None
        else:
            start = self.start
            stop = self.stop

        return self.query_compiler.search(
            self.query_compiler.get_config(self.backend),
            start,
            stop,
            score_field=self._score_field
        )

    def _do_search(self):
        return list(self.get_queryset())

    def _do_count(self):
        return self.get_queryset(for_count=True).count()

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

        query = self.query_compiler.search(self.query_compiler.get_config(self.backend), None, None)
        results = query.values(field_name).annotate(count=Count('pk')).order_by('-count')

        return OrderedDict([
            (result[field_name], result['count'])
            for result in results
        ])


class SQLiteSearchBackend(BaseSearchBackend):
    query_compiler_class = SQLiteSearchQueryCompiler
    autocomplete_query_compiler_class = SQLiteAutocompleteQueryCompiler
    results_class = SQLiteSearchResults
    rebuilder_class = SQLiteSearchRebuilder
    atomic_rebuilder_class = SQLiteSearchAtomicRebuilder

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
        for connection in [connection for connection in connections.all() if connection.vendor == 'sqlite']:
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


SearchBackend = SQLiteSearchBackend
