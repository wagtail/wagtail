from __future__ import absolute_import

import string

from django.db import models

from elasticsearch import Elasticsearch, NotFoundError, RequestError
from elasticsearch.helpers import bulk

from wagtail.wagtailsearch.backends.base import BaseSearch
from wagtail.wagtailsearch.indexed import Indexed

from .query import ElasticSearchQuery
from .document import ElasticSearchField, ElasticSearchType, ElasticSearchDocument


class ElasticSearchResults(object):
    """
    This represents a lazy set of results from running a query on an ElasticSearch backend.

    It's designed to work in a very similar way to Django QuerySets.
    """
    def __init__(self, backend, query):
        self.backend = backend
        self.query = query
        self.start = 0
        self.stop = None
        self._results_cache = None
        self._hit_count = None

    def _clone(self):
        klass = self.__class__
        new = klass(self.backend, self.query._clone())
        new.start = self.start
        new.stop = self.stop
        return new

    def _get_pks(self):
        """
        This gets a list of primary keys for the results of this query ordered
        by relevance.
        """
        # Get query
        query = self.query.to_es()

        # Params for elasticsearch query
        params = dict(
            index=self.backend.es_index,
            body=dict(query=query),
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
        return [pk[0] if isinstance(pk, list) else pk for pk in pks]

    def _do_count(self):
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

    def count(self):
        """
        This performs an Elastic search count query which returns how many
        results would be returned if this query was run for real.
        """
        if self._hit_count is None:
            if self._results_cache is not None:
                self._hit_count = len(self._results_cache)
            else:
                self._hit_count = self._do_count()
        return self._hit_count

    def _do_search(self):
        # Get list of PKs from ElasticSearch
        pks = self._get_pks()

        # Initialise results dictionary
        results = dict((str(pk), None) for pk in pks)

        # Find objects in database and add them to dict
        query_set = self.query.query_set.filter(pk__in=pks)
        for obj in query_set:
            results[str(obj.pk)] = obj

        # Return results in order given by ElasticSearch
        return [results[str(pk)] for pk in pks if results[str(pk)]]

    def _fetch_all(self):
        """
        This fetches all the results as a list of Django objects
        """
        if self._results_cache is None:
            self._results_cache = self._do_search()
        return self._results_cache

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
            # Return a single item
            if self._results_cache is not None:
                return self._results_cache[key]

            new.start = key
            new.stop = key + 1
            return list(new)[0]
  
    def __repr__(self):
        data = list(self[:21])
        if len(data) > 20:
            data[-1] = "...(remaining elements truncated)..."
        return repr(data)

    def __iter__(self):
        """
        Runs the query and returns an iterator for the results.
        """
        return iter(self._fetch_all())
  
    def __len__(self):
        """
        This runs the query and returns the amount of results returned
        This method may be very slow for large queries.
        """
        return len(self._fetch_all())


class ElasticSearch(BaseSearch):
    """
    This represents a connection to an instance of ElasticSearch.
    """
    def __init__(self, params):
        super(ElasticSearch, self).__init__(params)

        # Get settings
        self.es_urls = params.get('URLS', ['http://localhost:9200'])
        self.es_index = params.get('INDEX', 'wagtail')

        # Get ElasticSearch interface
        self.es = Elasticsearch(urls=self.es_urls)

    def reset_index(self):
        """
        This resets the index by deleting and recreating it.
        """
        # Delete old index
        try:
            self.es.indices.delete(self.es_index)
        except NotFoundError:
            pass

        # Settings
        INDEX_SETTINGS = {
            'settings': {
                'analysis': {
                    'analyzer': {
                        'ngram_analyzer': {
                            'type': 'custom',
                            'tokenizer': 'lowercase',
                            'filter': ['ngram']
                        },
                        'edgengram_analyzer': {
                            'type': 'custom',
                            'tokenizer': 'lowercase',
                            'filter': ['edgengram']
                        }
                    },
                    'tokenizer': {
                        'ngram_tokenizer': {
                            'type': 'nGram',
                            'min_gram': 3,
                            'max_gram': 15,
                        },
                        'edgengram_tokenizer': {
                            'type': 'edgeNGram',
                            'min_gram': 2,
                            'max_gram': 15,
                            'side': 'front'
                        }
                    },
                    'filter': {
                        'ngram': {
                            'type': 'nGram',
                            'min_gram': 3,
                            'max_gram': 15
                        },
                        'edgengram': {
                            'type': 'edgeNGram',
                            'min_gram': 1,
                            'max_gram': 15
                        }
                    }
                }
            }
        }

        # Create new index
        self.es.indices.create(self.es_index, INDEX_SETTINGS)

    def add_type(self, model):
        """
        This adds a mapping for a model to ElasticSearch to allow
        objects of that model to be indexed.
        """
        # Get ElasticSearchType object for this model
        es_type = ElasticSearchType(model)

        # Put mapping
        self.es.indices.put_mapping(
            index=self.es_index,
            doc_type=es_type.get_doc_type(),
            body=es_type.get_mapping()
        )

    def refresh_index(self):
        """
        This method refreshes the ElasticSearch index. This must be run
        in order for any newly indexed objects to appear in results.

        This is automatically run once per second by ElasticSearch so you
        only need to use this method if you plan on running queries
        immediately after indexing objects.
        """
        self.es.indices.refresh(self.es_index)

    def add(self, obj):
        """
        This adds an object to an index.

        Make sure the type has been added to the index before running
        this or weird things may happen!
        """
        # Make sure the object can be indexed
        if not self.object_can_be_indexed(obj):
            return

        # Get document
        es_doc = ElasticSearchDocument(obj)

        # Add to index
        self.es.index(
            self.es_index,
            es_doc.es_type.get_doc_type(),
            es_doc.build_document(),
            id=es_doc.get_id()
        )

    def add_bulk(self, obj_list):
        """
        This adds a bunch of objects to the index in one go.

        Roughly equivilant to:
        for obj in obj_list:
            self.add(obj)
        """
        # Group all objects by their type
        type_set = {}
        for obj in obj_list:
            # Object must be a decendant of Indexed and be a django model
            if not self.object_can_be_indexed(obj):
                continue

            # Get object type
            obj_type = obj._get_qualified_content_type_name()

            # If type is currently not in set, add it
            if obj_type not in type_set:
                type_set[obj_type] = []

            # Add object to set
            type_set[obj_type].append(ElasticSearchDocument(obj))

        # Loop through each type and bulk add them
        for type_name, es_docs in type_set.items():
            # Get list of actions
            actions = []
            for es_doc in es_docs:
                action = {
                    '_index': self.es_index,
                    '_type': type_name,
                    '_id': es_doc.get_id(),
                }
                action.update(es_doc.build_document())
                actions.append(action)

            yield type_name, len(es_docs)
            bulk(self.es, actions)

    def delete(self, obj):
        """
        This deletes an object from the index.

        Will fail silently if the object doesn't exist
        """
        # Object must be a decendant of Indexed and be a django model
        if not isinstance(obj, Indexed) or not isinstance(obj, models.Model):
            return

        # Delete document
        es_doc = ElasticSearchDocument(obj)
        try:
            self.es.delete(
                self.es_index,
                es_doc.es_type.get_doc_type(),
                es_doc.get_id(),
            )
        except NotFoundError:
            pass  # Document doesn't exist, ignore this exception

    def search(self, query_set, query_string, fields=None):
        """
        This runs a search query on the index.
        Returns an ElasticSearchResults object.
        """
        # Model must be a descendant of Indexed
        if not issubclass(query_set.model, Indexed):
            return query_set.none()

        # Clean up query string
        if query_string is not None:
            query_string = "".join([c for c in query_string if c not in string.punctuation])

        # Don't search using blank query strings (this upsets ElasticSearch)
        if query_string == "":
            return query_set.none()

        # Get fields
        if fields is None:
            fields = query_set.model.get_search_fields(exclude_filter=True).keys()

        # Return nothing if there are no fields
        if not fields:
            return query_set.none()

        # Return search results
        return ElasticSearchResults(self, ElasticSearchQuery(query_set, query_string, fields=fields))
