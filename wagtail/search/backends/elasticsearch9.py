from modelsearch.backends.elasticsearch9 import *  # noqa: F403
from modelsearch.backends.elasticsearch9 import (
    Elasticsearch9SearchBackend as _Elasticsearch9SearchBackend,
)

from wagtail.search.backends.deprecation import IndexOptionMixin


class Elasticsearch9SearchBackend(IndexOptionMixin, _Elasticsearch9SearchBackend):
    pass


SearchBackend = Elasticsearch9SearchBackend
