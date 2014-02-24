from django.conf.urls import patterns, url


urlpatterns = patterns(
    'wagtail.wagtailsearch.views',
    url(r'^$', 'search', name='wagtailsearch_search'),
    url(r'^suggest/$', 'search', {'use_json': True}, name='wagtailsearch_suggest'),
)
