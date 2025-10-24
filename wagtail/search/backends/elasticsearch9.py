from modelsearch.backends.elasticsearch9 import *  # noqa: F403
from modelsearch.backends.elasticsearch9 import (
    Elasticsearch9AutocompleteQueryCompiler as _Elasticsearch9AutocompleteQueryCompiler,
)
from modelsearch.backends.elasticsearch9 import (
    Elasticsearch9SearchBackend as _Elasticsearch9SearchBackend,
)
from modelsearch.backends.elasticsearch9 import (
    Elasticsearch9SearchQueryCompiler as _Elasticsearch9SearchQueryCompiler,
)

from wagtail.search.backends.deprecation import (
    IndexOptionMixin,
    LegacyContentTypeMatchMixin,
)


class Elasticsearch9SearchQueryCompiler(
    LegacyContentTypeMatchMixin, _Elasticsearch9SearchQueryCompiler
):
    pass


class Elasticsearch9AutocompleteQueryCompiler(
    LegacyContentTypeMatchMixin, _Elasticsearch9AutocompleteQueryCompiler
):
    pass


class Elasticsearch9SearchBackend(IndexOptionMixin, _Elasticsearch9SearchBackend):
    query_compiler_class = Elasticsearch9SearchQueryCompiler
    autocomplete_query_compiler_class = Elasticsearch9AutocompleteQueryCompiler


SearchBackend = Elasticsearch9SearchBackend
