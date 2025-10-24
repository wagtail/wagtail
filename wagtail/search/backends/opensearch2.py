from modelsearch.backends.opensearch2 import *  # noqa: F403
from modelsearch.backends.opensearch2 import (
    OpenSearch2AutocompleteQueryCompiler as _OpenSearch2AutocompleteQueryCompiler,
)
from modelsearch.backends.opensearch2 import (
    OpenSearch2SearchBackend as _OpenSearch2SearchBackend,
)
from modelsearch.backends.opensearch2 import (
    OpenSearch2SearchQueryCompiler as _OpenSearch2SearchQueryCompiler,
)

from wagtail.search.backends.deprecation import (
    IndexOptionMixin,
    LegacyContentTypeMatchMixin,
)


class OpenSearch2SearchQueryCompiler(
    LegacyContentTypeMatchMixin, _OpenSearch2SearchQueryCompiler
):
    pass


class OpenSearch2AutocompleteQueryCompiler(
    LegacyContentTypeMatchMixin, _OpenSearch2AutocompleteQueryCompiler
):
    pass


class OpenSearch2SearchBackend(IndexOptionMixin, _OpenSearch2SearchBackend):
    query_compiler_class = OpenSearch2SearchQueryCompiler
    autocomplete_query_compiler_class = OpenSearch2AutocompleteQueryCompiler


SearchBackend = OpenSearch2SearchBackend
