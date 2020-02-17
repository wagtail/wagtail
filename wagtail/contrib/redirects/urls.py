from django.urls import path, re_path

from wagtail.contrib.redirects import views

app_name = 'wagtailredirects'
urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add, name='add'),
    re_path(r'^(\d+)/$', views.edit, name='edit'),
    re_path(r'^(\d+)/delete/$', views.delete, name='delete'),
    re_path(r"^import/$", views.start_import, name="start_import"),
    re_path(r"^import/process/$", views.process_import, name="process_import"),
]
