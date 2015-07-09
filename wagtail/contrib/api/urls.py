from __future__ import absolute_import

from django.conf.urls import url, include

from . import api


urlpatterns = [
    url(r'^v1/', include(api.v1.get_urlpatterns(), namespace='wagtailapi_v1')),
]
