from django.conf.urls import patterns, url


urlpatterns = patterns(
    'wagtail.wagtailforms.views',
    url(r'^$', 'index', name='wagtailforms_index'),
    url(r'^submissions/(\d+)/$', 'list_submissions', name='wagtailforms_list_submissions'),

)
