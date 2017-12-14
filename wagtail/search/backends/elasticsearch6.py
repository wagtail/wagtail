from .elasticsearch5 import (
    Elasticsearch5Index, Elasticsearch5Mapping, Elasticsearch5SearchBackend,
    Elasticsearch5SearchQuery, Elasticsearch5SearchResults)


class Elasticsearch6Mapping(Elasticsearch5Mapping):
    pass

class Elasticsearch6Index(Elasticsearch5Index):
    pass


class Elasticsearch6SearchQuery(Elasticsearch5SearchQuery):
    mapping_class = Elasticsearch6Mapping


class Elasticsearch6SearchResults(Elasticsearch5SearchResults):
    pass


class Elasticsearch6SearchBackend(Elasticsearch5SearchBackend):
    mapping_class = Elasticsearch6Mapping
    index_class = Elasticsearch6Index
    query_class = Elasticsearch6SearchQuery
    results_class = Elasticsearch6SearchResults


SearchBackend = Elasticsearch6SearchBackend
