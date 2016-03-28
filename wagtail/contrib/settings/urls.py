from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(\w+)/(\w+)/$', views.edit_current_site, name='edit'),
    url(r'^(\d+)/(\w+)/(\w+)/$', views.edit, name='edit'),
]
