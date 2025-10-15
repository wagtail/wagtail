from modelsearch.backends.opensearch2 import *  # noqa: F403
from modelsearch.backends.opensearch2 import (
    OpenSearch2SearchBackend as _OpenSearch2SearchBackend,
)

from wagtail.search.backends.deprecation import IndexOptionMixin


class OpenSearch2SearchBackend(IndexOptionMixin, _OpenSearch2SearchBackend):
    pass


SearchBackend = OpenSearch2SearchBackend
