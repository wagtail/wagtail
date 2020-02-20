from django.urls import path, re_path

from wagtail.contrib.redirects import views

app_name = 'wagtailredirects'
urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add, name='add'),
    path('<int:redirect_id>/', views.edit, name='edit'),
    path('<int:redirect_id>/delete/', views.delete, name='delete'),
]
