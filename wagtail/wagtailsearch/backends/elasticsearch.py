from __future__ import absolute_import

from django.db import models
from django.conf import settings

from elasticsearch import Elasticsearch, NotFoundError, RequestError
from elasticsearch.helpers import bulk

from wagtail.wagtailsearch.backends.base import BaseSearch
from wagtail.wagtailsearch.indexed import Indexed

import string
import datetime


class FilterError(Exception):
    pass


class ElasticSearchQuery(object):
    """
    Represents a query to be run on an Elasticsearch backend.

    These queries combine the filters from a Django QuerySet with a query string and
    produce the JSON Query DSL code to be run on an ElasticSearch backend.
    """
    def __init__(self, query_set, query_string, fields=None, _es_type=None):
        self.query_set = query_set
        self.query_string = query_string
        self.fields = fields

        # Check if _es_type was provided and use if if so.
        # ElasticSearchType objects take a lot of work to create
        # so we should only make them when we need to.
        if _es_type is not None:
            self._es_type = _es_type
        else:
            self._es_type = ElasticSearchType(self.query_set.model)

    def _clone(self):
        klass = self.__class__
        return klass(self.query_set, self.query_string, fields=self.fields, _es_type=self._es_type)

    def _get_filters_from_where(self, where_node):
        """
        This method takes the filters from a Django Query and converts them
        to ElasticSearch format.
        """
        # Check if this is a leaf node
        if isinstance(where_node, tuple):
            field = where_node[0].col
            lookup = where_node[1]
            value = where_node[3]

            es_field = self._es_type.get_field(field)
            filter_field = es_field.get_filter_name()

            # Find lookup
            if lookup == 'exact':
                if value is None:
                    return {
                        'missing': {
                            'field': filter_field,
                        }
                    }
                else:
                    return {
                        'term': {
                            filter_field: es_field.convert_value(value)
                        }
                    }

            if lookup == 'isnull':
                if value:
                    return {
                        'missing': {
                            'field': filter_field,
                        }
                    }
                else:
                    return {
                        'not': {
                            'missing': {
                                'field': filter_field,
                            }
                        }
                    }

            if lookup in ['startswith', 'prefix']:
                return {
                    'prefix': {
                        filter_field: es_field.convert_value(value)
                    }
                }

            if lookup in ['gt', 'gte', 'lt', 'lte']:
                return {
                    'range': {
                        filter_field: {
                            lookup: es_field.convert_value(value),
                        }
                    }
                }

            if lookup == 'range':
                lower, upper = value

                return {
                    'range': {
                        filter_field: {
                            'gte': es_field.convert_value(lower),
                            'lte': es_field.convert_value(upper),
                        }
                    }
                }

            raise FilterError('Could not apply filter on ElasticSearch results "' + field + '__' + lookup + ' = ' + str(value) + '". Lookup "' + lookup + '"" not recognosed.')

        # Get child filters
        connector = where_node.connector
        child_filters = [self._get_filters_from_where(child) for child in where_node.children]
        child_filters = [child_filter for child_filter in child_filters if child_filter]

        # Connect them
        if child_filters:
            if len(child_filters) == 1:
                filter_out = child_filters[0]
            else:
                filter_out = {
                    connector.lower(): [
                        fil for fil in child_filters if fil is not None
                    ]
                }

            if where_node.negated:
                filter_out = {
                    'not': filter_out
                }

            return filter_out

    def _get_filters(self):
        """
        This method builds the 'filter' section of the query.
        """
        # Filters
        filters = []

        # Filter by content type
        filters.append({
            'prefix': {
                'content_type': self.query_set.model._get_qualified_content_type_name()
            }
        })

        # Apply filters from queryset
        query_set_filters = self._get_filters_from_where(self.query_set.query.where)
        if query_set_filters:
            filters.append(query_set_filters)

        return filters

    def to_es(self):
        """
        This method builds the ElasticSearch JSON Query DSL code for this query.
        """
        # Query
        if self.query_string is not None:
            query = {
                'query_string': {
                    'query': self.query_string,
                }
            }
        else:
            query = {
                'match_all': {}
            }

        # Fields
        if self.fields:
            query['query_string']['fields'] = self.fields

        # Filters
        filters = self._get_filters()
        if len(filters) == 1:
            query = {
                'filtered': {
                    'query': query,
                    'filter': filters[0],
                }
            }
        elif len(filters) > 1:
            query = {
                'filtered': {
                    'query': query,
                    'filter': {
                        'and': filters,
                    }
                }
            }

        return query


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


class ElasticSearchField(object):
    """
    This represents a field inside an ElasticSearchType.

    This has three jobs:
     - Find the ElasticSearch type for a particular field in a Django model.
     - Convert values to formats that ElasticSearch will recognise.
     - Produces mapping code for fields.
    """
    TYPE_MAP = {
        'TextField': 'string',
        'SlugField': 'string',
        'CharField': 'string',
        'PositiveIntegerField': 'integer',
        'BooleanField': 'boolean',
        'OneToOneField': 'string',
        'ForeignKey': 'string',
        'AutoField': 'integer',
        'DateField': 'date',
        'TimeField': 'date',
        'DateTimeField': 'date',
        'IntegerField': 'integer',
    }

    def __init__(self, name, **kwargs):
        self.name = name
        self.attname = kwargs['attname'] if 'attname' in kwargs else self.name
        self.search_field = kwargs['search'] if 'search' in kwargs else False
        self.filter_field = kwargs['filter'] if 'filter' in kwargs else False
        self.type = self.convert_type(kwargs['type']) if 'type' in kwargs else 'string'
        self.boost = kwargs['boost'] if 'boost' in kwargs else None
        self.predictive = kwargs['predictive'] if 'predictive' in kwargs else False
        self.es_extra = kwargs['es_extra'] if 'es_extra' in kwargs else {}

    def get_filter_name(self):
        return self.attname + '_filter'

    def get_search_name(self):
        return self.attname

    def can_be_indexed(self):
        """
        Returns true if this field can be indexed in ElasticSearch.
        """
        return self.type is not None

    def convert_type(self, django_type):
        """
        This takes a Django field type (eg, TextField, IntegerField) and
        converts it to an ElasticSearch type (eg, string, integer).

        Returns None if the type cannot be indexed.
        """
        # Lookup es type from TYPE_MAP
        if django_type in self.TYPE_MAP:
            return self.TYPE_MAP[django_type]

    def convert_value(self, value):
        """
        This converts a value to a format that can be sent to ElasticSearch.
        It uses the type of this field.
        """
        if value is None:
            return

        if self.type == 'string':
            return unicode(value)
        elif self.type == 'integer':
            return int(value)
        elif self.type == 'boolean':
            return bool(value)
        elif self.type == 'date':
            return value.isoformat()

    def get_search_mapping(self):
        mapping = {
            'type': self.type
        }

        if self.boost is not None:
            mapping['boost'] = self.boost

        if self.predictive:
            mapping['analyzer'] = 'edgengram_analyzer'

        if self.es_extra:
            mapping.update(self.es_extra)

        return mapping

    def get_filter_mapping(self):
        return {
            'type': self.type,
            'index': 'not_analyzed',
        }

    def get_mapping(self):
        if not self.can_be_indexed():
            return

        mappings = {}

        if self.search_field:
            mappings[self.get_search_name()] = self.get_search_mapping()

        if self.filter_field:
            mappings[self.get_filter_name()] = self.get_filter_mapping()

        return mappings


class ElasticSearchType(object):
    """
    This represents a Django model which can be indexed inside ElasticSearch.
    It provides helper methods to help build ES mappings for a Django model.
    """
    def __init__(self, model):
        self.model = model
        self._fields = None

    def get_doc_type(self):
        """
        Returns the value to use for the doc_type attribute when refering to this
        type in ElasticSearch requests.
        """
        return self.model._get_qualified_content_type_name()

    def _get_fields(self):
        # Get field list
        fields = self.model.get_search_fields()

        # Build ES fields
        fields = [
            (name, ElasticSearchField(name, **config))
            for name, config in fields.items()
        ]

        # Remove fields that can't be indexed
        fields = [(field.attname, field) for name, field in fields if field.can_be_indexed()]

        # Return
        return dict(fields)

    def get_fields(self):
        """
        Gets a mapping of fieldnames to ElasticSearchField objects.
        """
        # Do some caching to prevent having to keep building the field list
        if self._fields is None:
            self._fields = self._get_fields()
        return self._fields

    def get_field(self, name):
        """
        Returns an ElasticSearchField object for the specified field.
        """
        return self.get_fields()[name]

    def has_field(self, name):
        """
        Returns True if the specified field exists in this type.
        """
        return name in self.get_fields()

    def get_mapping(self):
        """
        This method builds a mapping for this type which can be sent to ElasticSearch using
        the put mapping API.
        """
        # Make field list
        fields = {
            'pk': {
                'type': 'string',
                'index': 'not_analyzed',
                'store': 'yes',
            },
            'content_type': {
                'type': 'string',
                'index': 'not_analyzed',
            },
        }

        for name, field in self.get_fields().items():
            fields.update(field.get_mapping().items())

        return {
            self.get_doc_type(): {
                'properties': fields,
            }
        }


class ElasticSearchDocument(object):
    """
    This represents a Django object to be indexed in ElasticSearch.
    """
    def __init__(self, obj):
        self.obj = obj
        self.es_type = ElasticSearchType(obj.__class__)

    def get_id(self):
        """
        This returns the value to be used in this documents 'id' field.

        This takes the objects "base content type name" and concatenates it
        with the objects primary key.

        See the description in "wagtail.search.indexed.Indexed._get_base_content_type_name"
        for info on what the "base content type name" is.
        """
        return self.obj._get_base_content_type_name() + ':' + str(self.obj.pk)

    def build_document(self):
        """
        This builds a JSON document in ElasticSearch Index API format for the object.
        """
        # Build document
        doc = {
            'pk': str(self.obj.pk),
            'content_type': self.obj._get_qualified_content_type_name(),
            'id': self.get_id(),
        }

        # Add fields
        for name, field in self.es_type.get_fields().items():
            if hasattr(self.obj, field.attname):
                # Get field value
                value = getattr(self.obj, field.attname)

                # Check if this field is callable
                if hasattr(value, '__call__'):
                    # Call it
                    value = value()

                # Convert it
                value = field.convert_value(value)

                # Add to document
                if field.search_field:
                    doc[field.get_search_name()] = value
                if field.filter_field:
                    doc[field.get_filter_name()] = value

        return doc


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
