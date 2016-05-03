from __future__ import absolute_import, unicode_literals

from threading import current_thread

from wagtail.wagtailcore.request_cache import RequestCache


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

    _request_caches = {}

    def process_request(self, request):
        # The RequestCache object is keyed on the current thread because each request is processed on a single thread,
        # allowing us to retrieve the correct RequestCache object in the other functions.
        self._request_caches[current_thread()] = RequestCache()

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
        return cls._request_caches.get(current_thread())

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
        Delete the current request's cache object to avoid leaking memory.
        """
        cache = cls._request_caches.pop(current_thread(), None)
        del cache
