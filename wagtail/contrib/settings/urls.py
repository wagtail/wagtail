from django.urls import path

from . import views

app_name = 'wagtailsettings'
urlpatterns = [
    path('<str:app_name>/<str:model_name>/', views.edit_current_site, name='edit'),
    path('<str:app_name>/<str:model_name>/<int:site_pk>/', views.edit, name='edit'),
]
