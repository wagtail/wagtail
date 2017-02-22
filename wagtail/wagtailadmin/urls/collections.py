from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wagtail.wagtailadmin.views import collections

urlpatterns = [
    url(r'^$', collections.Index.as_view(), name='index'),
    url(r'^(\d+)/$', collections.Index.as_view(), name='index'),
    url(r'^(\d+)?/add/$', collections.Create.as_view(), name='add'),
    url(r'^(\d+)/edit/$', collections.Edit.as_view(), name='edit'),
    url(r'^(\d+)/delete/$', collections.Delete.as_view(), name='delete'),
]
