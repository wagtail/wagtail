from django.conf.urls import url
from wagtail.wagtailsearch.views import search, SearchView

from wagtail.wagtailcore.models import Page


urlpatterns = [
    url(r'^$', SearchView.as_view(queryset=Page.objects.live()), name='wagtailsearch_search'),
    url(r'^suggest/$', search, {'use_json': True}, name='wagtailsearch_suggest'),
]
