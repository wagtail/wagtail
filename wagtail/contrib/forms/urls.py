from django.urls import path, re_path

from wagtail.contrib.forms.views import (
    DeleteSubmissionsView, FormPagesListView, get_submissions_list_view)

app_name = 'wagtailforms'
urlpatterns = [
    path('', FormPagesListView.as_view(), name='index'),
    re_path(r'^submissions/(?P<page_id>\d+)/$', get_submissions_list_view, name='list_submissions'),
    re_path(r'^submissions/(?P<page_id>\d+)/delete/$', DeleteSubmissionsView.as_view(), name='delete_submissions')
]
