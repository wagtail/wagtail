from wagtail.search.backends.elasticsearch7 import (
    Elasticsearch7AutocompleteQueryCompiler,
    Elasticsearch7Index,
    Elasticsearch7Mapping,
    Elasticsearch7SearchBackend,
    Elasticsearch7SearchQueryCompiler,
    Elasticsearch7SearchResults,
)


class Elasticsearch8Mapping(Elasticsearch7Mapping):
    pass


class Elasticsearch8Index(Elasticsearch7Index):
    pass


class Elasticsearch8SearchQueryCompiler(Elasticsearch7SearchQueryCompiler):
    mapping_class = Elasticsearch8Mapping


class Elasticsearch8SearchResults(Elasticsearch7SearchResults):
    pass


class Elasticsearch8AutocompleteQueryCompiler(Elasticsearch7AutocompleteQueryCompiler):
    mapping_class = Elasticsearch8Mapping


class Elasticsearch8SearchBackend(Elasticsearch7SearchBackend):
    mapping_class = Elasticsearch8Mapping
    index_class = Elasticsearch8Index
    query_compiler_class = Elasticsearch8SearchQueryCompiler
    autocomplete_query_compiler_class = Elasticsearch8AutocompleteQueryCompiler
    results_class = Elasticsearch8SearchResults


SearchBackend = Elasticsearch8SearchBackend
