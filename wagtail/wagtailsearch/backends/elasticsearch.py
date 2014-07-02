from __future__ import absolute_import

import json
import warnings

from django.db import models

from elasticsearch import Elasticsearch, NotFoundError, RequestError
from elasticsearch.helpers import bulk

from wagtail.wagtailsearch.backends.base import BaseSearch
from wagtail.wagtailsearch.indexed import Indexed
from wagtail.wagtailsearch.utils import normalise_query_string


class ElasticSearchQuery(object):
    def __init__(self, model, query_string, fields=None, filters={}):
        self.model = model
        self.query_string = query_string
        self.fields = fields or ['_all']
        self.filters = filters

    def _get_filters(self):
        # Filters
        filters = []

        # Filter by content type
        filters.append({
            'prefix': {
                'content_type': self.model.indexed_get_content_type()
            }
        })

        # Extra filters
        if self.filters:
            for key, value in self.filters.items():
                if '__' in key:
                    field, lookup = key.split('__')
                else:
                    field = key
                    lookup = None

                if lookup is None:
                    if value is None:
                        filters.append({
                            'missing': {
                                'field': field,
                            }
                        })
                    else:
                        filters.append({
                            'term': {
                                field: value
                            }
                        })

                if lookup in ['startswith', 'prefix']:
                    filters.append({
                        'prefix': {
                            field: value
                        }
                    })

                if lookup in ['gt', 'gte', 'lt', 'lte']:
                    filters.append({
                        'range': {
                            field: {
                                lookup: value,
                            }
                        }
                    })

                if lookup == 'range':
                    lower, upper = value
                    filters.append({
                        'range': {
                            field: {
                                'gte': lower,
                                'lte': upper,
                            }
                        }
                    })

        return filters

    def to_es(self):
        # Query
        query = {
            'query_string': {
                'query': self.query_string,
            }
        }

        # Fields
        if self.fields:
            query['query_string']['fields'] = self.fields

        # Filters
        filters = self._get_filters()

        return {
            'filtered': {
                'query': query,
                'filter': {
                    'and': filters,
                }
            }
        }

    def __repr__(self):
        return json.dumps(self.to_es())


class ElasticSearchResults(object):
    def __init__(self, backend, query, prefetch_related=None):
        self.backend = backend
        self.query = query
        self.prefetch_related = prefetch_related
        self.start = 0
        self.stop = None
        self._results_cache = None
        self._count_cache = None

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
        new = klass(self.backend, self.query, prefetch_related=self.prefetch_related)
        new.start = self.start
        new.stop = self.stop
        return new

    def _do_search(self):
        # Params for elasticsearch query
        params = dict(
            index=self.backend.es_index,
            body=dict(query=self.query.to_es()),
            _source=False,
            fields='pk',
            from_=self.start,
        )

        # Add size if set
        if self.stop is not None:
            params['size'] = self.stop - self.start

        # Send to ElasticSearch
        hits = self.backend.es.search(**params)

        # Get pks from results
        pks = [hit['fields']['pk'] for hit in hits['hits']['hits']]

        # ElasticSearch 1.x likes to pack pks into lists, unpack them if this has happened
        pks = [pk[0] if isinstance(pk, list) else pk for pk in pks]

        # Initialise results dictionary
        results = dict((str(pk), None) for pk in pks)

        # Get queryset
        queryset = self.query.model.objects.filter(pk__in=pks)

        # Add prefetch related
        if self.prefetch_related:
            for prefetch in self.prefetch_related:
                queryset = queryset.prefetch_related(prefetch)

        # Find objects in database and add them to dict
        for obj in queryset:
            results[str(obj.pk)] = obj

        # Return results in order given by ElasticSearch
        return [results[str(pk)] for pk in pks if results[str(pk)]]

    def _do_count(self):
        # Get query
        query = self.query.to_es()

        # Elasticsearch 1.x
        count = self.backend.es.count(
            index=self.backend.es_index,
            body=dict(query=query),
        )

        # ElasticSearch 0.90.x fallback
        if not count['_shards']['successful'] and "No query registered for [query]]" in count['_shards']['failures'][0]['reason']:
            count = self.backend.es.count(
                index=self.backend.es_index,
                body=query,
            )

        # Get count
        hit_count = count['count']

        # Add limits
        hit_count -= self.start
        if self.stop is not None:
            hit_count = min(hit_count, self.stop - self.start)

        return max(hit_count, 0)

    def results(self):
        if self._results_cache is None:
            self._results_cache = self._do_search()
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
            start = int(key.start) if key.start else None
            stop = int(key.stop) if key.stop else None
            new._set_limits(start, stop)

            # Copy results cache
            if self._results_cache is not None:
                new._results_cache = self._results_cache[key]

            return new
        else:
            if self._results_cache is not None:
                return self._results_cache[key]

            new.start = key
            new.stop = key + 1
            return list(new)[0]

    def __iter__(self):
        return iter(self.results())

    def __len__(self):
        return len(self.results())

    def __repr__(self):
        data = list(self[:21])
        if len(data) > 20:
            data[-1] = "...(remaining elements truncated)..."
        return repr(data)


class ElasticSearch(BaseSearch):
    def __init__(self, params):
        super(ElasticSearch, self).__init__(params)

        # Get settings
        self.es_urls = params.pop('URLS', ['http://localhost:9200'])
        self.es_index = params.pop('INDEX', 'wagtail')
        self.es_timeout = params.pop('TIMEOUT', 5)
        self.es_force_new = params.pop('FORCE_NEW', False)

        # Get ElasticSearch interface
        # Any remaining params are passed into the ElasticSearch constructor
        self.es = Elasticsearch(
            urls=self.es_urls,
            timeout=self.es_timeout,
            force_new=self.es_force_new,
            **params)

    def reset_index(self):
        # Delete old index
        try:
            self.es.indices.delete(self.es_index)
        except NotFoundError:
            pass

        # Settings
        INDEX_SETTINGS = {
            "settings": {
                "analysis": {
                    "analyzer": {
                        "ngram_analyzer": {
                            "type": "custom",
                            "tokenizer": "lowercase",
                            "filter": ["ngram"]
                        },
                        "edgengram_analyzer": {
                            "type": "custom",
                            "tokenizer": "lowercase",
                            "filter": ["edgengram"]
                        }
                    },
                    "tokenizer": {
                        "ngram_tokenizer": {
                            "type": "nGram",
                            "min_gram": 3,
                            "max_gram": 15,
                        },
                        "edgengram_tokenizer": {
                            "type": "edgeNGram",
                            "min_gram": 2,
                            "max_gram": 15,
                            "side": "front"
                        }
                    },
                    "filter": {
                        "ngram": {
                            "type": "nGram",
                            "min_gram": 3,
                            "max_gram": 15
                        },
                        "edgengram": {
                            "type": "edgeNGram",
                            "min_gram": 1,
                            "max_gram": 15
                        }
                    }
                }
            }
        }

        # Create new index
        self.es.indices.create(self.es_index, INDEX_SETTINGS)

    def add_type(self, model):
        # Get type name
        content_type = model.indexed_get_content_type()

        # Get indexed fields
        indexed_fields = model.indexed_get_indexed_fields()

        # Make field list
        fields = {
            "pk": dict(type="string", index="not_analyzed", store="yes"),
            "content_type": dict(type="string"),
        }
        fields.update(indexed_fields)

        # Put mapping
        self.es.indices.put_mapping(index=self.es_index, doc_type=content_type, body={
            content_type: {
                "properties": fields,
            }
        })

    def refresh_index(self):
        self.es.indices.refresh(self.es_index)

    def add(self, obj):
        # Make sure the object can be indexed
        if not self.object_can_be_indexed(obj):
            return

        # Build document
        doc = obj.indexed_build_document()

        # Add to index
        self.es.index(self.es_index, obj.indexed_get_content_type(), doc, id=doc["id"])

    def add_bulk(self, obj_list):
        # Group all objects by their type
        type_set = {}
        for obj in obj_list:
            # Object must be a decendant of Indexed and be a django model
            if not self.object_can_be_indexed(obj):
                continue

            # Get object type
            obj_type = obj.indexed_get_content_type()

            # If type is currently not in set, add it
            if obj_type not in type_set:
                type_set[obj_type] = []

            # Add object to set
            type_set[obj_type].append(obj.indexed_build_document())

        # Loop through each type and bulk add them
        for type_name, type_objects in type_set.items():
            # Get list of actions
            actions = []
            for obj in type_objects:
                action = {
                    '_index': self.es_index,
                    '_type': type_name,
                    '_id': obj['id'],
                }
                action.update(obj)
                actions.append(action)

            bulk(self.es, actions)

    def delete(self, obj):
        # Object must be a decendant of Indexed and be a django model
        if not isinstance(obj, Indexed) or not isinstance(obj, models.Model):
            return

        # Delete document
        try:
            self.es.delete(
                self.es_index,
                obj.indexed_get_content_type(),
                obj.indexed_get_document_id(),
            )
        except NotFoundError:
            pass  # Document doesn't exist, ignore this exception

    def search(self, query_string, model, fields=None, filters={}, prefetch_related=[]):
        # Model must be a descendant of Indexed and be a django model
        if not issubclass(model, Indexed) or not issubclass(model, models.Model):
            return []

        # Normalise query string
        query_string = normalise_query_string(query_string)

        # Check that theres still a query string after the clean up
        if not query_string:
            return []

        # Return search results
        return ElasticSearchResults(self, ElasticSearchQuery(model, query_string, fields=fields, filters=filters), prefetch_related=prefetch_related)
