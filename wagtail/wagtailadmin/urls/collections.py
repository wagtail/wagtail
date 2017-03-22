from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wagtail.wagtailadmin.views import collections

urlpatterns = [
    url(r'^$', collections.Index.as_view(), name='index'),
    url(r'^(\d+)/$', collections.Index.as_view(), name='parent_index'),
    url(r'^(\d+)/add/$', collections.Create.as_view(), name='add_child'),
    url(r'^(\d+)/edit/$', collections.Edit.as_view(), name='edit'),
    url(r'^(\d+)/move/$', collections.Move.as_view(), name='move_root'),
    url(r'^(\d+)/move/(\d+)/$', collections.Move.as_view(), name='move'),
    url(r'^(\d+)/move/(\d+)/confirm/$', collections.MoveConfirm.as_view(), name='move_confirm'),
    url(r'^(\d+)/delete/$', collections.Delete.as_view(), name='delete'),
    url(r'^choose-collection/$', collections.Index.as_view(), name='choose_collection'),
    url(r'^choose-collection/(\d+)/$', collections.Index.as_view(), name='choose_collection_child'),
    url(r'^choose-collection-search/$', collections.Index.as_view(), name='choose_collection_search'),
]
