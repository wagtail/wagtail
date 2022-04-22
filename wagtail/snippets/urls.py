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
    # legacy URLs that could potentially collide if the pk matches one of the reserved names above
    # ('add', 'edit' etc) - redirect to the unambiguous version
    path("<slug:app_label>/<slug:model_name>/<str:pk>/", snippets.redirect_to_edit),
    path(
        "<slug:app_label>/<slug:model_name>/<str:pk>/delete/",
        snippets.redirect_to_delete,
    ),
    path(
        "<slug:app_label>/<slug:model_name>/<str:pk>/usage/", snippets.redirect_to_usage
    ),
]
