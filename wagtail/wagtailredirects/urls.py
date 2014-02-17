from django.conf.urls import patterns, url


urlpatterns = patterns('wagtail.wagtailredirects.views',
    url(r'^$', 'index', name='wagtailredirects_index'),
    url(r'^(\d+)/$', 'edit', name='wagtailredirects_edit_redirect'),
    url(r'^(\d+)/delete/$', 'delete', name='wagtailredirects_delete_redirect'),
    url(r'^add/$', 'add', name='wagtailredirects_add_redirect'),
)
