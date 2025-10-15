from modelsearch.backends.opensearch3 import *  # noqa: F403
from modelsearch.backends.opensearch3 import (
    OpenSearch3SearchBackend as _OpenSearch3SearchBackend,
)

from wagtail.search.backends.deprecation import IndexOptionMixin


class OpenSearch3SearchBackend(IndexOptionMixin, _OpenSearch3SearchBackend):
    pass


SearchBackend = OpenSearch3SearchBackend
