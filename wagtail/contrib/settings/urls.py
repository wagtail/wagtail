from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(\w+)/(\w+)/$', views.edit, name='wagtailsettings_edit'),
]
