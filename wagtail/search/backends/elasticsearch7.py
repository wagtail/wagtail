from modelsearch.backends.elasticsearch7 import *  # noqa: F403
from modelsearch.backends.elasticsearch7 import (
    Elasticsearch7SearchBackend as _Elasticsearch7SearchBackend,
)

from wagtail.search.backends.deprecation import IndexOptionMixin


class Elasticsearch7SearchBackend(IndexOptionMixin, _Elasticsearch7SearchBackend):
    pass


SearchBackend = Elasticsearch7SearchBackend
