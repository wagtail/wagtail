from modelsearch.backends.elasticsearch8 import *  # noqa: F403
from modelsearch.backends.elasticsearch8 import (
    Elasticsearch8SearchBackend as _Elasticsearch8SearchBackend,
)

from wagtail.search.backends.deprecation import IndexOptionMixin


class Elasticsearch8SearchBackend(IndexOptionMixin, _Elasticsearch8SearchBackend):
    pass


SearchBackend = Elasticsearch8SearchBackend
