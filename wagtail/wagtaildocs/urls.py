from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wagtail.wagtaildocs.views import serve

urlpatterns = [
    url(r'^(\d+)/(.*)$', serve.serve, name='wagtaildocs_serve'),
    url(r'^authenticate_with_password/(\d+)/$', serve.authenticate_with_password,
        name='wagtaildocs_authenticate_with_password'),
]
