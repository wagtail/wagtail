import functools

from django.conf.urls import url, include

from wagtail.utils.urlpatterns import decorate_urlpatterns


class WagtailAPIRouter(object):
    def __init__(self, url_namespace):
        self.url_namespace = url_namespace
        self._endpoints = {}

    def register_endpoint(self, name, class_):
        self._endpoints[name] = class_

    def wrap_view(self, func):
        @functools.wraps(func)
        def wrapped(request, *args, **kwargs):
            request.wagtailapi_router = self
            return func(request, *args, **kwargs)

        return wrapped

    def get_urlpatterns(self):
        urlpatterns = []

        for name, class_ in self._endpoints.items():
            pattern = url(
                r'^{}/'.format(name),
                include(class_.get_urlpatterns(), namespace=name)
            )
            urlpatterns.append(pattern)

        decorate_urlpatterns(urlpatterns, self.wrap_view)

        return urlpatterns

    @property
    def urls(self):
        return self.get_urlpatterns(), self.url_namespace, self.url_namespace
