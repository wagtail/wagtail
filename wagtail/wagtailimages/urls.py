from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wagtail.wagtailimages.views.serve import serve

urlpatterns = [
    url(r'^([^/]*)/(\d*)/([^/]*)/[^/]*$', serve, name='wagtailimages_serve'),
]
