from django.conf.urls import patterns, url


urlpatterns = patterns("wagtail.wagtailsearch.views.frontend",
    url(r"^$", "search", name="wagtailsearch_search"),
    url(r"^suggest/$", "suggest", name="wagtailsearch_suggest"),
)
