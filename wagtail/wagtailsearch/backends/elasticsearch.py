from __future__ import absolute_import

from django.db import models

from elasticsearch import Elasticsearch, NotFoundError

from wagtail.wagtailsearch.backends.base import BaseSearch
from wagtail.wagtailsearch.indexed import Indexed

import string


class ElasticSearchResults(object):
    def __init__(self, backend, model, query_string, fields=None, filters={}, prefetch_related=[]):
        self.backend = backend
        self.model = model
        self.query_string = query_string
        self.fields = fields
        self.filters = filters
        self.prefetch_related = prefetch_related

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

    def _get_query(self):
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
            'query': {
                'filtered': {
                    'query': query,
                    'filter': {
                        'and': filters,
                    }
                }
            }
        }

    def _get_results_pks(self, offset=0, limit=None):
        query = self._get_query()
        query['query']['from'] = offset
        if limit is not None:
            query['query']['size'] = limit

        hits = self.backend.es.search(
            index=self.backend.es_index,
            body=query,
            _source=False,
            fields='pk',
        )

        return [hit['fields']['pk'][0] for hit in hits['hits']['hits']]

    def _get_count(self):
        query = self._get_query()
        count = self.backend.es.count(
            index=self.backend.es_index,
            body=query,
        )

        return count['count']

    def __getitem__(self, key):
        if isinstance(key, slice):
            # Get primary keys
            pk_list_unclean = self._get_results_pks(key.start, key.stop - key.start)

            # Remove duplicate keys (and preserve order)
            seen_pks = set()
            pk_list = []
            for pk in pk_list_unclean:
                if pk not in seen_pks:
                    seen_pks.add(pk)
                    pk_list.append(pk)

            # Get results
            results = self.model.objects.filter(pk__in=pk_list)

            # Prefetch related
            for prefetch in self.prefetch_related:
                results = results.prefetch_related(prefetch)

            # Put results into a dictionary (using primary key as the key)
            results_dict = dict((str(result.pk), result) for result in results)

            # Build new list with items in the correct order
            results_sorted = [results_dict[str(pk)] for pk in pk_list if str(pk) in results_dict]

            # Return the list
            return results_sorted
        else:
            # Return a single item
            pk = self._get_results_pks(key, key + 1)[0]
            return self.model.objects.get(pk=pk)

    def __len__(self):
        return self._get_count()


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
        fields = dict({
            "pk": dict(type="string", index="not_analyzed", store="yes"),
            "content_type": dict(type="string"),
        }.items() + indexed_fields.items())

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
        # TODO: Make this work with new elastic search module
        for obj in obj_list:
            self.add(obj)
        return
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
        results = []
        for type_name, type_objects in type_set.items():
            results.append((type_name, len(type_objects)))
            self.es.bulk_index(self.es_index, type_name, type_objects)
        return results

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

        # Clean up query string
        query_string = "".join([c for c in query_string if c not in string.punctuation])

        # Check that theres still a query string after the clean up
        if not query_string:
            return []

        # Return search results
        return ElasticSearchResults(self, model, query_string, fields=fields, filters=filters, prefetch_related=prefetch_related)
