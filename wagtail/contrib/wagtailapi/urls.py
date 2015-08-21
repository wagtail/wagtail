from __future__ import absolute_import

from django.conf.urls import url, include

from .endpoints import endpoints


urlpatterns = [
    url(r'^v1/pages/', include(endpoints[0].get_urlpatterns(), namespace='wagtailapi_v1_pages')),
    url(r'^v1/images/', include(endpoints[1].get_urlpatterns(), namespace='wagtailapi_v1_images')),
    url(r'^v1/documents/', include(endpoints[2].get_urlpatterns(), namespace='wagtailapi_v1_documents'))
]
