from django.db import models
from django.conf import settings

from pyelasticsearch.exceptions import ElasticHttpNotFoundError
from elasticutils import get_es, S

from wagtail.wagtailsearch.backends.base import BaseSearch
from wagtail.wagtailsearch.indexed import Indexed

import string


class ElasticSearchResults(object):
    def __init__(self, model, query, prefetch_related=[]):
        self.model = model
        self.query = query
        self.count = query.count()
        self.prefetch_related = prefetch_related

    def __getitem__(self, key):
        if isinstance(key, slice):
            # Get primary keys
            pk_list_unclean = [result._source["pk"] for result in self.query[key]]

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
            results_dict = {str(result.pk): result for result in results}

            # Build new list with items in the correct order
            results_sorted = [results_dict[str(pk)] for pk in pk_list if str(pk) in results_dict]

            # Return the list
            return results_sorted
        else:
            # Return a single item
            pk = self.query[key]._source["pk"]
            return self.model.objects.get(pk=pk)

    def __len__(self):
        return self.count


class ElasticSearch(BaseSearch):
    def __init__(self, params):
        super(ElasticSearch, self).__init__(params)

        # Get settings
        self.es_urls = params.get('URLS', ['http://localhost:9200'])
        self.es_index = params.get('INDEX', 'wagtail')

        # Get ElasticSearch interface
        self.es = get_es(urls=self.es_urls)
        self.s = S().es(urls=self.es_urls).indexes(self.es_index)

    def reset_index(self):
        # Delete old index
        try:
            self.es.delete_index(self.es_index)
        except ElasticHttpNotFoundError:
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
        self.es.create_index(self.es_index, INDEX_SETTINGS)

    def add_type(self, model):
        # Make sure that the model is indexed
        if not model.indexed:
            return

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
        self.es.put_mapping(self.es_index, content_type, {
            content_type: {
                "properties": fields,
            }
        })

    def refresh_index(self):
        self.es.refresh(self.es_index)

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
        results = []
        for type_name, type_objects in type_set.items():
            results.append((type_name, len(type_objects)))
            self.es.bulk_index(self.es_index, type_name, type_objects)
        return results

    def delete(self, obj):
        # Object must be a decendant of Indexed and be a django model
        if not isinstance(obj, Indexed) or not isinstance(obj, models.Model):
            return

        # Get ID for document
        doc_id = obj.indexed_get_document_id()

        # Delete document
        try:
            self.es.delete(self.es_index, obj.indexed_get_content_type(), doc_id)
        except ElasticHttpNotFoundError:
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

        # Query
        if fields:
            query = self.s.query_raw({
                "query_string": {
                    "query": query_string,
                    "fields": fields,
                }
            })
        else:
            query = self.s.query_raw({
                "query_string": {
                    "query": query_string,
                }
            })

        # Filter results by this content type
        query = query.filter(content_type__prefix=model.indexed_get_content_type())

        # Extra filters
        if filters:
            query = query.filter(**filters)

        # Return search results
        return ElasticSearchResults(model, query, prefetch_related=prefetch_related)
