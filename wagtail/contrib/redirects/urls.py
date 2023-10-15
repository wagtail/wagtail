from django.urls import path

from wagtail.contrib.redirects import views

app_name = "wagtailredirects"
urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("results/", views.Index.as_view(results_only=True), name="index_results"),
    path("add/", views.Create.as_view(), name="add"),
    path("<int:pk>/", views.Edit.as_view(), name="edit"),
    path("<int:pk>/delete/", views.Delete.as_view(), name="delete"),
    path("import/", views.start_import, name="start_import"),
    path("import/process/", views.process_import, name="process_import"),
    path("report", views.RedirectsReportView.as_view(), name="report"),
]
