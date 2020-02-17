from django.urls import path, re_path

from wagtail.contrib.redirects import views

app_name = 'wagtailredirects'
urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add, name='add'),
    re_path(r'^(\d+)/$', views.edit, name='edit'),
    re_path(r'^(\d+)/delete/$', views.delete, name='delete'),
]
