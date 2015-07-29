from django.conf.urls import url
from wagtail.wagtailsearch.views import queries


urlpatterns = [
    url(r"^queries/chooser/$", queries.chooser, name="wagtailsearch_queries_chooser"),
    url(r"^queries/chooser/results/$", queries.chooserresults, name="wagtailsearch_queries_chooserresults"),
]
