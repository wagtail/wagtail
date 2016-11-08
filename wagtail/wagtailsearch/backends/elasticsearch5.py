from __future__ import absolute_import, unicode_literals

from .elasticsearch2 import Elasticsearch2SearchBackend


class Elasticsearch5SearchBackend(Elasticsearch2SearchBackend):
    pass


SearchBackend = Elasticsearch5SearchBackend
