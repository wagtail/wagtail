from __future__ import absolute_import, unicode_literals

import functools

from django.utils.functional import cached_property


# Need to inherit from object explicitly, to turn ``cached_classmethod`` in to
# a new-style class. WeakKeyDictionary is an old-style class, which do not
# support descriptors.
class cached_classmethod(dict):
    """
    Cache the result of a no-arg class method.
    .. code-block:: python
        class Foo(object):
            @cached_classmethod
            def bar(cls):
                # Some expensive computation
                return 'baz'
    Similar to ``@lru_cache``, but the cache is per-class, stores a single
    value, and thus doesn't fill up; where as ``@lru_cache`` is global across
    all classes, and could fill up if too many classes were used.
    """

    def __init__(self, fn):
        self.fn = fn
        functools.update_wrapper(self, fn)

    def __get__(self, instance, owner):
        """ Get the class_cache for this type when accessed """
        return self[owner]

    def __missing__(self, cls):
        """ Make a new class_cache on cache misses """
        value = _cache(self, cls, self.fn)
        self[cls] = value
        return value


class _cache(object):
    """ Calls the real class method behind when called, caching the result """
    def __init__(self, cache, cls, fn):
        self.cache = cache
        self.cls = cls
        self.fn = fn
        functools.update_wrapper(self, fn)

    @cached_property
    def value(self):
        """ Generate the cached value """
        return self.fn(self.cls)

    def __call__(self):
        """ Get the cached value """
        return self.value

    def cache_clear(self):
        """ Clear the cached value. """
        # Named after lru_cache.cache_clear
        self.cache.pop(self.cls, None)
