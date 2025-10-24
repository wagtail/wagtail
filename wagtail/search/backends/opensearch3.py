from modelsearch.backends.opensearch3 import *  # noqa: F403
from modelsearch.backends.opensearch3 import (
    OpenSearch3AutocompleteQueryCompiler as _OpenSearch3AutocompleteQueryCompiler,
)
from modelsearch.backends.opensearch3 import (
    OpenSearch3SearchBackend as _OpenSearch3SearchBackend,
)
from modelsearch.backends.opensearch3 import (
    OpenSearch3SearchQueryCompiler as _OpenSearch3SearchQueryCompiler,
)

from wagtail.search.backends.deprecation import (
    IndexOptionMixin,
    LegacyContentTypeMatchMixin,
)


class OpenSearch3SearchQueryCompiler(
    LegacyContentTypeMatchMixin, _OpenSearch3SearchQueryCompiler
):
    pass


class OpenSearch3AutocompleteQueryCompiler(
    LegacyContentTypeMatchMixin, _OpenSearch3AutocompleteQueryCompiler
):
    pass


class OpenSearch3SearchBackend(IndexOptionMixin, _OpenSearch3SearchBackend):
    query_compiler_class = OpenSearch3SearchQueryCompiler
    autocomplete_query_compiler_class = OpenSearch3AutocompleteQueryCompiler


SearchBackend = OpenSearch3SearchBackend
