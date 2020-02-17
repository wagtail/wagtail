from django.urls import re_path

from . import views

app_name = 'wagtailsettings'
urlpatterns = [
    re_path(r'^(\w+)/(\w+)/$', views.edit_current_site, name='edit'),
    re_path(r'^(\w+)/(\w+)/(\d+)/$', views.edit, name='edit'),
]
