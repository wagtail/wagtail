from django.urls import path

from wagtail.contrib.redirects import views


app_name = 'wagtailredirects'
urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add, name='add'),
    path('<int:redirect_id>/', views.edit, name='edit'),
    path('<int:redirect_id>/delete/', views.delete, name='delete'),
    path('import/', views.start_import, name="start_import"),
    path('import/process/', views.process_import, name="process_import"),
    path('report', views.RedirectsReportView.as_view(), name="report"),
]
