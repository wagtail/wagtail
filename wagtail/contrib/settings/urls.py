from django.urls import path

from . import views

app_name = "wagtailsettings"
urlpatterns = [
    path(
        "<slug:app_name>/<slug:model_name>/",
        views.redirect_to_relevant_instance,
        name="edit",
    ),
    path(
        "<slug:app_name>/<slug:model_name>/<int:pk>/",
        views.EditView.as_view(),
        name="edit",
    ),
]
