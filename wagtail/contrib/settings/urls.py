from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(\w+)/(\w+)/$', views.edit_current_site, name='edit'),
    url(r'^(\w+)/(\w+)/(\d+)/$', views.edit, name='edit'),
]
