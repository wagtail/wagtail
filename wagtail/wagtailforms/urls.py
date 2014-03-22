from django.conf.urls import patterns, url


urlpatterns = patterns(
    'wagtail.wagtailforms.views',
    url(r'^$', 'index', name='wagtailforms_index'),

    #url(r'^choose/$', 'chooser.choose', name='wagtailsnippets_choose_generic'),
    #url(r'^choose/(\w+)/(\w+)/$', 'chooser.choose', name='wagtailsnippets_choose'),
    
    #url(r'^(\w+)/(\w+)/$', 'snippets.list', name='wagtailsnippets_list'),
    #url(r'^(\w+)/(\w+)/new/$', 'snippets.create', name='wagtailsnippets_create'),
    #url(r'^(\w+)/(\w+)/(\d+)/$', 'snippets.edit', name='wagtailsnippets_edit'),
)
