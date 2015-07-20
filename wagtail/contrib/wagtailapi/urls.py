from __future__ import absolute_import

from django.conf.urls import url, include

from .endpoints import PagesAPIEndpoint, ImagesAPIEndpoint, DocumentsAPIEndpoint


v1 = [
    url(r'^pages/', include(PagesAPIEndpoint.get_urlpatterns(), namespace='pages')),
    url(r'^images/', include(ImagesAPIEndpoint.get_urlpatterns(), namespace='images')),
    url(r'^documents/', include(DocumentsAPIEndpoint.get_urlpatterns(), namespace='documents'))
]


urlpatterns = [
    url(r'^v1/', include(v1, namespace='wagtailapi_v1')),
]
