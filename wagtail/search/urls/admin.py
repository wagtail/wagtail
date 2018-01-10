from django.conf.urls import url

from wagtail.search.views import queries

app_name = 'wagtailsearch_admin'
urlpatterns = [
    url(r"^queries/chooser/$", queries.chooser, name="queries_chooser"),
    url(r"^queries/chooser/results/$", queries.chooserresults, name="queries_chooserresults"),
]
