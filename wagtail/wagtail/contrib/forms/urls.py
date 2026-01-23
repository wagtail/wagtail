from django.urls import path

from wagtail.contrib.forms.views import (
    DeleteSubmissionsView,
    FormPagesListView,
    get_submissions_list_view,
)

app_name = "wagtailforms"
urlpatterns = [
    path("", FormPagesListView.as_view(), name="index"),
    path(
        "results/", FormPagesListView.as_view(results_only=True), name="index_results"
    ),
    path(
        "submissions/<int:page_id>/", get_submissions_list_view, name="list_submissions"
    ),
    path(
        "submissions/<int:page_id>/results/",
        get_submissions_list_view,
        {"results_only": True},
        name="list_submissions_results",
    ),
    path(
        "submissions/<int:page_id>/delete/",
        DeleteSubmissionsView.as_view(),
        name="delete_submissions",
    ),
]
