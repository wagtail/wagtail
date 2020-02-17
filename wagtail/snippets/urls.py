from django.urls import path, re_path

from wagtail.snippets.views import chooser, snippets

app_name = 'wagtailsnippets'
urlpatterns = [
    path('', snippets.index, name='index'),

    path('choose/', chooser.choose, name='choose_generic'),
    re_path(r'^choose/(\w+)/(\w+)/$', chooser.choose, name='choose'),
    re_path(r'^choose/(\w+)/(\w+)/([^/]+?)/$', chooser.chosen, name='chosen'),

    re_path(r'^(\w+)/(\w+)/$', snippets.list, name='list'),
    re_path(r'^(\w+)/(\w+)/add/$', snippets.create, name='add'),
    re_path(r'^(\w+)/(\w+)/([^/]+?)/$', snippets.edit, name='edit'),
    re_path(r'^(\w+)/(\w+)/multiple/delete/$', snippets.delete, name='delete-multiple'),
    re_path(r'^(\w+)/(\w+)/([^/]+?)/delete/$', snippets.delete, name='delete'),
    re_path(r'^(\w+)/(\w+)/([^/]+?)/usage/$', snippets.usage, name='usage'),
]
