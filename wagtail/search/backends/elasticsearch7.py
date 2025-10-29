from modelsearch.backends.elasticsearch7 import *  # noqa: F403
from modelsearch.backends.elasticsearch7 import (
    Elasticsearch7AutocompleteQueryCompiler as _Elasticsearch7AutocompleteQueryCompiler,
)
from modelsearch.backends.elasticsearch7 import (
    Elasticsearch7SearchBackend as _Elasticsearch7SearchBackend,
)
from modelsearch.backends.elasticsearch7 import (
    Elasticsearch7SearchQueryCompiler as _Elasticsearch7SearchQueryCompiler,
)

from wagtail.search.backends.deprecation import (
    IndexOptionMixin,
    LegacyContentTypeMatchMixin,
)


class Elasticsearch7SearchQueryCompiler(
    LegacyContentTypeMatchMixin, _Elasticsearch7SearchQueryCompiler
):
    pass


class Elasticsearch7AutocompleteQueryCompiler(
    LegacyContentTypeMatchMixin, _Elasticsearch7AutocompleteQueryCompiler
):
    pass


class Elasticsearch7SearchBackend(IndexOptionMixin, _Elasticsearch7SearchBackend):
    query_compiler_class = Elasticsearch7SearchQueryCompiler
    autocomplete_query_compiler_class = Elasticsearch7AutocompleteQueryCompiler


SearchBackend = Elasticsearch7SearchBackend
