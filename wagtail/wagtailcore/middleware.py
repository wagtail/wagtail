from __future__ import absolute_import, unicode_literals

from threading import current_thread

from django.core.cache.backends.locmem import LocMemCache, _caches, _expire_info, _locks


class SiteMiddleware(object):

    def process_request(self, request):
        """
        Set request.site to contain the Site object responsible for handling this request,
        according to hostname matching rules
        """
        # wagtail.wagtailcore.models imports RequestCacheMiddleware, so we can't import Site from there at
        # compile time without triggering a circular import.
        from wagtail.wagtailcore.models import Site

        try:
            request.site = Site.find_for_request(request)
        except Site.DoesNotExist:
            request.site = None


class RequestCacheMiddleware(object):
    """
    Creates a cache instance that persists only for the duration of the current request.
    """

    _request_cache = {}

    def process_request(self, request):
        thread = current_thread()
        cache_name = 'RequestCacheMiddleware@{}'.format(hash(thread))
        self._request_cache[thread] = LocMemCache(name=cache_name, params={})
        # LocMemCache doesn't save the name that gets passed into it, so we have to do it ourselves.
        self._request_cache[thread].name = cache_name

    def process_response(self, request, response):
        self.delete_cache()
        return response

    def process_exception(self, request, exception):
        self.delete_cache()

    @classmethod
    def get_cache(cls):
        """
        Retrieve the current request's cache.

        Returns None if RequestCacheMiddleware is not currently installed via MIDDLEWARE_CLASSES, or if there is no
        active request.
        """
        return cls._request_cache.get(current_thread())

    @classmethod
    def clear_cache(cls):
        """
        Clear the current request's cache.
        """
        cache = cls.get_cache()
        if cache:
            cache.clear()

    @classmethod
    def delete_cache(cls):
        """
        Delete the current request's cache object. This is used to avoid memory leaks as threads get cycled.
        """
        cache = cls._request_cache.pop(current_thread(), None)
        # Creating a LocMemCache object permanently stores references to it in the following global dictionaries.
        # Since we need to create a new LocMemCache object for each request, this leads to a memory leak unless we
        # explicitly destroy all references to the LocMemCache object we created in __init__().
        if cache:
            del _caches[cache.name]
            del _expire_info[cache.name]
            del _locks[cache.name]
