from django.urls import path

from . import views

app_name = "wagtailsettings"
urlpatterns = [
    path("<slug:app_name>/<slug:model_name>/", views.edit_current_site, name="edit"),
    path("<slug:app_name>/<slug:model_name>/<int:site_pk>/", views.edit, name="edit"),
]
