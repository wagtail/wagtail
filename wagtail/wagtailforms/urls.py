from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wagtail.wagtailforms import views

urlpatterns = [
    url(r'^$', views.ListFormPages.as_view(), name='index'),
    url(r'^submissions/(?P<page_id>\d+)/$', views.ListSubmissions.as_view(), name='list_submissions'),
    url(r'^submissions/(?P<page_id>\d+)/delete/$', views.DeleteSubmissions.as_view(), name='delete_submissions')
]
