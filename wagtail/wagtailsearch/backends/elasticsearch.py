from __future__ import absolute_import

import json

from six.moves.urllib.parse import urlparse

from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.helpers import bulk

from wagtail.wagtailsearch.backends.base import BaseSearch, BaseSearchQuery, BaseSearchResults
from wagtail.wagtailsearch.index import SearchField, FilterField, class_is_indexed


class ElasticSearchMapping(object):
    TYPE_MAP = {
        'AutoField': 'integer',
        'BinaryField': 'binary',
        'BooleanField': 'boolean',
        'CharField': 'string',
        'CommaSeparatedIntegerField': 'string',
        'DateField': 'date',
        'DateTimeField': 'date',
        'DecimalField': 'double',
        'FileField': 'string',
        'FilePathField': 'string',
        'FloatField': 'double',
        'IntegerField': 'integer',
        'BigIntegerField': 'long',
        'IPAddressField': 'string',
        'GenericIPAddressField': 'string',
        'NullBooleanField': 'boolean',
        'OneToOneField': 'integer',
        'PositiveIntegerField': 'integer',
        'PositiveSmallIntegerField': 'integer',
        'SlugField': 'string',
        'SmallIntegerField': 'integer',
        'TextField': 'string',
        'TimeField': 'date',
    }

    def __init__(self, model):
        self.model = model

    def get_document_type(self):
        return self.model.indexed_get_content_type()

    def get_field_mapping(self, field):
        mapping = {'type': self.TYPE_MAP.get(field.get_type(self.model), 'string')}

        if isinstance(field, SearchField):
            if field.boost:
                mapping['boost'] = field.boost

            if field.partial_match:
                mapping['index_analyzer'] = 'edgengram_analyzer'

            mapping['include_in_all'] = True
        elif isinstance(field, FilterField):
            mapping['index'] = 'not_analyzed'
            mapping['include_in_all'] = False

        if 'es_extra' in field.kwargs:
            for key, value in field.kwargs['es_extra'].items():
                mapping[key] = value

        return field.get_index_name(self.model), mapping

    def get_mapping(self):
        # Make field list
        fields = {
            'pk': dict(type='string', index='not_analyzed', store='yes', include_in_all=False),
            'content_type': dict(type='string', index='not_analyzed', include_in_all=False),
            '_partials': dict(type='string', index_analyzer='edgengram_analyzer', include_in_all=False),
        }

        fields.update(dict(
            self.get_field_mapping(field) for field in self.model.get_search_fields()
        ))

        return {
            self.get_document_type(): {
                'properties': fields,
            }
        }

    def get_document_id(self, obj):
        return obj.indexed_get_toplevel_content_type() + ':' + str(obj.pk)

    def get_document(self, obj):
        # Build document
        doc = dict(pk=str(obj.pk), content_type=self.model.indexed_get_content_type())
        partials = []
        for field in self.model.get_search_fields():
            value = field.get_value(obj)

            doc[field.get_index_name(self.model)] = value

            # Check if this field should be added into _partials
            if isinstance(field, SearchField) and field.partial_match:
                partials.append(value)

        # Add partials to document
        doc['_partials'] = partials

        return doc

    def __repr__(self):
        return '<ElasticSearchMapping: %s>' % (self.model.__name__, )


class ElasticSearchQuery(BaseSearchQuery):
    def _process_lookup(self, field, lookup, value):
        # Get the name of the field in the index
        field_index_name = field.get_index_name(self.queryset.model)

        if lookup == 'exact':
            if value is None:
                return {
                    'missing': {
                        'field': field_index_name,
                    }
                }
            else:
                return {
                    'term': {
                        field_index_name: value,
                    }
                }

        if lookup == 'isnull':
            if value:
                return {
                    'missing': {
                        'field': field_index_name,
                    }
                }
            else:
                return {
                    'not': {
                        'missing': {
                            'field': field_index_name,
                        }
                    }
                }

        if lookup in ['startswith', 'prefix']:
            return {
                'prefix': {
                    field_index_name: value,
                }
            }

        if lookup in ['gt', 'gte', 'lt', 'lte']:
            return {
                'range': {
                    field_index_name: {
                        lookup: value,
                    }
                }
            }

        if lookup == 'range':
            lower, upper = value

            return {
                'range': {
                    field_index_name: {
                        'gte': lower,
                        'lte': upper,
                    }
                }
            }

        if lookup == 'in':
            return {
                'terms': {
                    field_index_name: list(value),
                }
            }

    def _connect_filters(self, filters, connector, negated):
        if filters:
            if len(filters) == 1:
                filter_out = filters[0]
            else:
                filter_out = {
                    connector.lower(): [
                        fil for fil in filters if fil is not None
                    ]
                }

            if negated:
                filter_out = {
                    'not': filter_out
                }

            return filter_out

    def to_es(self):
        # Query
        if self.query_string is not None:
            fields = self.fields or ['_all', '_partials']

            if len(fields) == 1:
                query = {
                    'match': {
                        fields[0]: self.query_string,
                    }
                }
            else:
                query = {
                    'multi_match': {
                        'query': self.query_string,
                        'fields': fields,
                    }
                }
        else:
            query = {
                'match_all': {}
            }

        # Filters
        filters = []

        # Filter by content type
        filters.append({
            'prefix': {
                'content_type': self.queryset.model.indexed_get_content_type()
            }
        })

        # Apply filters from queryset
        queryset_filters = self._get_filters_from_queryset()
        if queryset_filters:
            filters.append(queryset_filters)

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

    def __repr__(self):
        return json.dumps(self.to_es())


class ElasticSearchResults(BaseSearchResults):
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
        pks = [hit['fields']['pk'][0] for hit in hits['hits']['hits']]

        # Initialise results dictionary
        results = dict((str(pk), None) for pk in pks)

        # Find objects in database and add them to dict
        queryset = self.query.queryset.filter(pk__in=pks)
        for obj in queryset:
            results[str(obj.pk)] = obj

        # Return results in order given by ElasticSearch
        return [results[str(pk)] for pk in pks if results[str(pk)]]

    def _do_count(self):
        # Get query
        query = self.query.to_es()

        # Get count
        hit_count = self.backend.es.count(
            index=self.backend.es_index,
            body=dict(query=query),
        )['count']

        # Add limits
        hit_count -= self.start
        if self.stop is not None:
            hit_count = min(hit_count, self.stop - self.start)

        return max(hit_count, 0)


class ElasticSearch(BaseSearch):
    def __init__(self, params):
        super(ElasticSearch, self).__init__(params)

        # Get settings
        self.es_hosts = params.pop('HOSTS', None)
        self.es_urls = params.pop('URLS', ['http://localhost:9200'])
        self.es_index = params.pop('INDEX', 'wagtail')
        self.es_timeout = params.pop('TIMEOUT', 10)

        # If HOSTS is not set, convert URLS setting to HOSTS
        if self.es_hosts is None:
            self.es_hosts = []

            for url in self.es_urls:
                parsed_url = urlparse(url)

                use_ssl = parsed_url.scheme == 'https'
                port = parsed_url.port or (443 if use_ssl else 80)

                http_auth = None
                if parsed_url.username is not None and parsed_url.password is not None:
                    http_auth = (parsed_url.username, parsed_url.password)

                self.es_hosts.append({
                    'host': parsed_url.hostname,
                    'port': port,
                    'url_prefix': parsed_url.path,
                    'use_ssl': use_ssl,
                    'http_auth': http_auth,
                })

        # Get ElasticSearch interface
        # Any remaining params are passed into the ElasticSearch constructor
        self.es = Elasticsearch(
            hosts=self.es_hosts,
            timeout=self.es_timeout,
            **params)

    def reset_index(self):
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
                            'filter': ['asciifolding', 'ngram']
                        },
                        'edgengram_analyzer': {
                            'type': 'custom',
                            'tokenizer': 'lowercase',
                            'filter': ['asciifolding', 'edgengram']
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
        # Get mapping
        mapping = ElasticSearchMapping(model)

        # Put mapping
        self.es.indices.put_mapping(index=self.es_index, doc_type=mapping.get_document_type(), body=mapping.get_mapping())

    def refresh_index(self):
        self.es.indices.refresh(self.es_index)

    def add(self, obj):
        # Make sure the object can be indexed
        if not class_is_indexed(obj.__class__):
            return

        # Get mapping
        mapping = ElasticSearchMapping(obj.__class__)

        # Add document to index
        self.es.index(self.es_index, mapping.get_document_type(), mapping.get_document(obj), id=mapping.get_document_id(obj))

    def add_bulk(self, model, obj_list):
        if not class_is_indexed(model):
            return

        # Get mapping
        mapping = ElasticSearchMapping(model)
        doc_type = mapping.get_document_type()

        # Create list of actions
        actions = []
        for obj in obj_list:
            # Create the action
            action = {
                '_index': self.es_index,
                '_type': doc_type,
                '_id': mapping.get_document_id(obj),
            }
            action.update(mapping.get_document(obj))
            actions.append(action)

        # Run the actions
        bulk(self.es, actions)

    def delete(self, obj):
        # Make sure the object can be indexed
        if not class_is_indexed(obj.__class__):
            return

        # Get mapping
        mapping = ElasticSearchMapping(obj.__class__)

        # Delete document
        try:
            self.es.delete(
                self.es_index,
                mapping.get_document_type(),
                mapping.get_document_id(obj),
            )
        except NotFoundError:
            pass  # Document doesn't exist, ignore this exception

    def _search(self, queryset, query_string, fields=None):
        return ElasticSearchResults(self, ElasticSearchQuery(queryset, query_string, fields=fields))
