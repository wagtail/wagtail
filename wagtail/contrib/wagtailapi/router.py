import functools

from django.conf.urls import url, include

from wagtail.utils.urlpatterns import decorate_urlpatterns


class WagtailAPIRouter(object):
    def __init__(self, url_namespace):
        self.url_namespace = url_namespace
        self._endpoints = {}

    def register_endpoint(self, name, class_):
        self._endpoints[name] = class_

    def get_model_endpoint(self, model):
        for name, class_ in self._endpoints.items():
            if issubclass(model, class_.model):
                return name, class_

    def get_object_detail_urlpath(self, model, pk):
        endpoint = self.get_model_endpoint(model)

        if endpoint:
            endpoint_name, endpoint_class = endpoint[0], endpoint[1]
            url_namespace = self.url_namespace + ':' + endpoint_name
            return endpoint_class.get_object_detail_urlpath(model, pk, namespace=url_namespace)

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
