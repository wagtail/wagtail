from django.urls import path

from wagtail.search.views import queries


app_name = 'wagtailsearch_admin'
urlpatterns = [
    path("queries/chooser/", queries.chooser, name="queries_chooser"),
    path("queries/chooser/results/", queries.chooserresults, name="queries_chooserresults"),
]
