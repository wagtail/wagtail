from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wagtail.wagtailsites import views

urlpatterns = [
    url(r'^$', views.Index.as_view(), name='index'),
    url(r'^add/$', views.Create.as_view(), name='add'),
    url(r'^(\d+)/$', views.Edit.as_view(), name='edit'),
    url(r'^(\d+)/delete/$', views.Delete.as_view(), name='delete'),
]
