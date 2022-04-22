from django.urls import path

from wagtail.snippets.views import chooser, snippets

app_name = "wagtailsnippets"
urlpatterns = [
    path("", snippets.Index.as_view(), name="index"),
    path(
        "choose/<slug:app_label>/<slug:model_name>/",
        chooser.ChooseView.as_view(),
        name="choose",
    ),
    path(
        "choose/<slug:app_label>/<slug:model_name>/results/",
        chooser.ChooseResultsView.as_view(),
        name="choose_results",
    ),
    path(
        "choose/<slug:app_label>/<slug:model_name>/chosen/<str:pk>/",
        chooser.ChosenView.as_view(),
        name="chosen",
    ),
]
