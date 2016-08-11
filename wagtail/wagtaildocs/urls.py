from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wagtail.wagtaildocs.views import serve

urlpatterns = [
    url(r'^(\d+)/(.*)$', serve.serve, name='wagtaildocs_serve'),
]
