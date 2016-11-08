from __future__ import absolute_import, unicode_literals

from .elasticsearch2 import (
    Elasticsearch2Mapping, Elasticsearch2SearchBackend, Elasticsearch2SearchQuery,
    Elasticsearch2SearchResults)


class Elasticsearch5Mapping(Elasticsearch2Mapping):
    keyword_type = 'keyword'
    text_type = 'text'
    set_index_not_analyzed_on_filter_fields = False


class Elasticsearch5SearchQuery(Elasticsearch2SearchQuery):
    mapping_class = Elasticsearch5Mapping


class Elasticsearch5SearchResults(Elasticsearch2SearchResults):
    fields_param_name = 'stored_fields'


class Elasticsearch5SearchBackend(Elasticsearch2SearchBackend):
    mapping_class = Elasticsearch5Mapping
    query_class = Elasticsearch5SearchQuery
    results_class = Elasticsearch5SearchResults


SearchBackend = Elasticsearch5SearchBackend
