from django.urls import path

from wagtail.contrib.search_promotions import views

app_name = "wagtailsearchpromotions"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("results/", views.IndexView.as_view(results_only=True), name="index_results"),
    path("add/", views.add, name="add"),
    path("<int:query_id>/", views.edit, name="edit"),
    path("<int:query_id>/delete/", views.delete, name="delete"),
    path("queries/chooser/", views.chooser, name="chooser"),
    path(
        "queries/chooser/results/",
        views.chooserresults,
        name="chooserresults",
    ),
]
