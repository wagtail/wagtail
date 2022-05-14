from django.urls import path

from wagtail.contrib.forms.views import (
    FormPagesListView,
    get_submissions_list_view,
)

app_name = "wagtailforms"
urlpatterns = [
    path("", FormPagesListView.as_view(), name="index"),
    path(
        "submissions/<int:page_id>/", get_submissions_list_view, name="list_submissions"
    )
]
