from django.conf.urls import url

from wagtail.search.views import search

app_name = 'wagtailsearch_frontend'
urlpatterns = [
    url(r'^$', search, name='wagtailsearch_search'),
    url(r'^suggest/$', search, {'use_json': True}, name='wagtailsearch_suggest'),
]
