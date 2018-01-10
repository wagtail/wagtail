import functools

from django.conf.urls import include, url

from wagtail.utils.urlpatterns import decorate_urlpatterns


class WagtailAPIRouter:
    """
    A class that provides routing and cross-linking for a collection
    of API endpoints
    """
    def __init__(self, url_namespace):
        self.url_namespace = url_namespace
        self._endpoints = {}

    def register_endpoint(self, name, class_):
        self._endpoints[name] = class_

    def get_model_endpoint(self, model):
        """
        Finds the endpoint in the API that represents a model

        Returns a (name, endpoint_class) tuple. Or None if an
        endpoint is not found.
        """
        for name, class_ in self._endpoints.items():
            if issubclass(model, class_.model):
                return name, class_

    def get_model_listing_urlpath(self, model):
        """
        Returns a URL path (excluding scheme and hostname) to the listing
        page of a model

        Returns None if the model is not represented by any endpoints.
        """
        endpoint = self.get_model_endpoint(model)

        if endpoint:
            endpoint_name, endpoint_class = endpoint[0], endpoint[1]
            url_namespace = self.url_namespace + ':' + endpoint_name
            return endpoint_class.get_model_listing_urlpath(model, namespace=url_namespace)

    def get_object_detail_urlpath(self, model, pk):
        """
        Returns a URL path (excluding scheme and hostname) to the detail
        page of an object.

        Returns None if the object is not represented by any endpoints.
        """
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
                include((class_.get_urlpatterns(), name), namespace=name)
            )
            urlpatterns.append(pattern)

        decorate_urlpatterns(urlpatterns, self.wrap_view)

        return urlpatterns

    @property
    def urls(self):
        """
        A shortcut to allow quick registration of the API in a URLconf.

        Use with Django's include() function:

            url(r'api/', include(myapi.urls)),
        """
        return self.get_urlpatterns(), self.url_namespace, self.url_namespace
