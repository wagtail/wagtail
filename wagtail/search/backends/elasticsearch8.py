from modelsearch.backends.elasticsearch8 import *  # noqa: F403
from modelsearch.backends.elasticsearch8 import (
    Elasticsearch8AutocompleteQueryCompiler as _Elasticsearch8AutocompleteQueryCompiler,
)
from modelsearch.backends.elasticsearch8 import (
    Elasticsearch8SearchBackend as _Elasticsearch8SearchBackend,
)
from modelsearch.backends.elasticsearch8 import (
    Elasticsearch8SearchQueryCompiler as _Elasticsearch8SearchQueryCompiler,
)

from wagtail.search.backends.deprecation import (
    IndexOptionMixin,
    LegacyContentTypeMatchMixin,
)


class Elasticsearch8SearchQueryCompiler(
    LegacyContentTypeMatchMixin, _Elasticsearch8SearchQueryCompiler
):
    pass


class Elasticsearch8AutocompleteQueryCompiler(
    LegacyContentTypeMatchMixin, _Elasticsearch8AutocompleteQueryCompiler
):
    pass


class Elasticsearch8SearchBackend(IndexOptionMixin, _Elasticsearch8SearchBackend):
    query_compiler_class = Elasticsearch8SearchQueryCompiler
    autocomplete_query_compiler_class = Elasticsearch8AutocompleteQueryCompiler


SearchBackend = Elasticsearch8SearchBackend
