from django.urls import path

from wagtail.contrib.redirects import views

app_name = "wagtailredirects"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("results/", views.IndexView.as_view(results_only=True), name="index_results"),
    path("add/", views.CreateView.as_view(), name="add"),
    path("<int:redirect_id>/", views.EditView.as_view(), name="edit"),
    path("<int:redirect_id>/delete/", views.DeleteView.as_view(), name="delete"),
    path("import/", views.start_import, name="start_import"),
    path("import/process/", views.process_import, name="process_import"),
]
