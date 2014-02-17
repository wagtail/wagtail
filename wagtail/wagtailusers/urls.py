from django.conf.urls import patterns, url

urlpatterns = patterns(
    'wagtail.wagtailusers.views',
    url(r'^$', 'users.index', name='wagtailusers_index'),
    url(r'^new/$', 'users.create', name='wagtailusers_create'),
    url(r'^(\d+)/$', 'users.edit', name='wagtailusers_edit'),
)
