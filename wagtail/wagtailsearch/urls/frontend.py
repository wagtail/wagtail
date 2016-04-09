from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wagtail.wagtailsearch.views import search

urlpatterns = [
    url(r'^$', search, name='wagtailsearch_search'),
    url(r'^suggest/$', search, {'use_json': True}, name='wagtailsearch_suggest'),
]
