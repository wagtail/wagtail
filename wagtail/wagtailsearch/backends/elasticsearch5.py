from __future__ import absolute_import, unicode_literals

from .elasticsearch2 import (
    Elasticsearch2Mapping, Elasticsearch2SearchBackend, Elasticsearch2SearchQuery)


class Elasticsearch5Mapping(Elasticsearch2Mapping):
    keyword_type = 'keyword'
    text_type = 'text'


class Elasticsearch5SearchQuery(Elasticsearch2SearchQuery):
    mapping_class = Elasticsearch5Mapping


class Elasticsearch5SearchBackend(Elasticsearch2SearchBackend):
    mapping_class = Elasticsearch5Mapping
    query_class = Elasticsearch5SearchQuery


SearchBackend = Elasticsearch5SearchBackend
