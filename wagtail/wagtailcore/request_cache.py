from __future__ import absolute_import, unicode_literals

from uuid import uuid4

from django.core.cache.backends.base import BaseCache
from django.core.cache.backends.locmem import LocMemCache
from django.utils.synch import RWLock


# Global in-memory store of cache data. Keyed by name, to provides multiple named local memory caches.
_caches = {}
_expire_info = {}
_locks = {}


class RequestCache(LocMemCache):
    """
    RequestCache is a customized LocMemCache with a destructor, ensuring that creating and destroying
    RequestCache objects over and over doesn't leak memory.
    """

    def __init__(self):
        # We explicitly do not call super() here, because while we want BaseCache.__init__() to run, we *don't*
        # want LocMemCache.__init__() to run.
        BaseCache.__init__(self, {})

        # Use a name that is guaranteed to be unique for each RequestCache instance. This ensures that it will
        # always be safe to call del _caches[self.name] in the destructor, even when multiple threads do so at the
        # same time.
        self.name = uuid4()
        self._cache = _caches.setdefault(self.name, {})
        self._expire_info = _expire_info.setdefault(self.name, {})
        self._lock = _locks.setdefault(self.name, RWLock())

    def __del__(self):
        del _caches[self.name]
        del _expire_info[self.name]
        del _locks[self.name]
