from django.urls import path

from wagtail.contrib.search_promotions import views
from wagtail.contrib.search_promotions.views.reports import SearchTermsReportView

app_name = "wagtailsearchpromotions"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("results/", views.IndexView.as_view(results_only=True), name="index_results"),
    path("add/", views.CreateView.as_view(), name="add"),
    path("<int:query_id>/", views.EditView.as_view(), name="edit"),
    path("<int:query_id>/delete/", views.DeleteView.as_view(), name="delete"),
    path("queries/chooser/", views.chooser, name="chooser"),
    path(
        "queries/chooser/results/",
        views.chooserresults,
        name="chooserresults",
    ),
    path("reports/search-terms/", SearchTermsReportView.as_view(), name="search_terms"),
    path(
        "reports/search-terms/results/",
        SearchTermsReportView.as_view(results_only=True),
        name="search_terms_results",
    ),
]
