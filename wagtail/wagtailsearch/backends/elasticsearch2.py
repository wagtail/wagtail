from __future__ import absolute_import, unicode_literals

from .elasticsearch import (
    ElasticsearchIndex, ElasticsearchMapping, ElasticsearchSearchBackend, ElasticsearchSearchQuery,
    ElasticsearchSearchResults)


class Elasticsearch2Mapping(ElasticsearchMapping):
    pass


class Elasticsearch2Index(ElasticsearchIndex):
    pass


class Elasticsearch2SearchQuery(ElasticsearchSearchQuery):
    mapping_class = Elasticsearch2Mapping


class Elasticsearch2SearchResults(ElasticsearchSearchResults):
    pass


class Elasticsearch2SearchBackend(ElasticsearchSearchBackend):
    mapping_class = Elasticsearch2Mapping
    index_class = Elasticsearch2Index
    query_class = Elasticsearch2SearchQuery
    results_class = Elasticsearch2SearchResults


SearchBackend = Elasticsearch2SearchBackend
