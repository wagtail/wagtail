from django.conf.urls import url, include

from .endpoints import PagesAPIEndpoint, ImagesAPIEndpoint, DocumentsAPIEndpoint


class API(object):
    def __init__(self, endpoints):
        self.endpoints = endpoints

    def get_urlpatterns(self):
        return [
            url(r'^%s/' % name, include(endpoint.get_urlpatterns(), namespace=name))
            for name, endpoint in self.endpoints.items()
        ]


v1 = API({
    'pages': PagesAPIEndpoint,
    'images': ImagesAPIEndpoint,
    'documents': DocumentsAPIEndpoint,
})
