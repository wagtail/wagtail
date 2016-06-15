from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wagtail.wagtailusers.views import users

urlpatterns = [
    url(r'^$', users.index, name='index'),
    url(r'^add/$', users.create, name='add'),
    url(r'^([^\/]+)/$', users.edit, name='edit'),
]
