from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wagtail.wagtailforms import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^submissions/(\d+)/$', views.list_submissions, name='list_submissions'),
    url(r'^submissions/(\d+)/(\d+)/delete/$', views.delete_submission, name='delete_submission')
]
