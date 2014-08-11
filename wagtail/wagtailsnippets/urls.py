from django.conf.urls import url
from wagtail.wagtailsnippets.views import chooser, snippets


urlpatterns = [
    url(r'^$', snippets.index, name='wagtailsnippets_index'),

    url(r'^choose/$', chooser.choose, name='wagtailsnippets_choose_generic'),
    url(r'^choose/(\w+)/(\w+)/$', chooser.choose, name='wagtailsnippets_choose'),
    url(r'^choose/(\w+)/(\w+)/(\d+)/$', chooser.chosen, name='wagtailsnippets_chosen'),

    url(r'^(\w+)/(\w+)/$', snippets.list, name='wagtailsnippets_list'),
    url(r'^(\w+)/(\w+)/new/$', snippets.create, name='wagtailsnippets_create'),
    url(r'^(\w+)/(\w+)/(\d+)/$', snippets.edit, name='wagtailsnippets_edit'),
    url(r'^(\w+)/(\w+)/(\d+)/delete/$', snippets.delete, name='wagtailsnippets_delete'),
    url(r'^(\w+)/(\w+)/(\d+)/usage/$', snippets.usage, name='wagtailsnippets_usage'),
]
