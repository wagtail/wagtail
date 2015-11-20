"""
Contains application administration URLs.
"""
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^pages/revisions/(?P<page_id>\d+)/$', views.page_revisions, name='page_revisions'),
    url(r'^pages/preview/(?P<revision_id>\d+)/$', views.preview_page_version, name='preview_page_version'),
    url(r'^pages/diff/(?P<revision_id>\d+)/$', views.preview_page_diff, name='preview_page_diff'),
    url(r'^pages/diff/(?P<revision_id>\d+)/(?P<diff_id>\d+)/$', views.preview_page_diff, name='preview_page_diff'),
    url(r'^pages/revert/(?P<revision_id>\d+)/$', views.confirm_page_reversion, name='confirm_page_reversion'),
]
