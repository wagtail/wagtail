from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wagtail.wagtailsnippets.views import chooser, snippets

urlpatterns = [
    url(r'^$', snippets.index, name='index'),

    url(r'^choose/$', chooser.choose, name='choose_generic'),
    url(r'^choose/(\w+)/(\w+)/$', chooser.choose, name='choose'),
    url(r'^choose/(\w+)/(\w+)/(\d+)/$', chooser.chosen, name='chosen'),

    url(r'^(\w+)/(\w+)/$', snippets.list, name='list'),
    url(r'^(\w+)/(\w+)/add/$', snippets.create, name='add'),
    url(r'^(\w+)/(\w+)/(\d+)/$', snippets.edit, name='edit'),
    url(r'^(\w+)/(\w+)/(\d+)/delete/$', snippets.delete, name='delete'),
    url(r'^(\w+)/(\w+)/(\d+)/usage/$', snippets.usage, name='usage'),
]
