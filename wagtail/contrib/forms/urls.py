from django.conf.urls import url

from wagtail.contrib.forms.views import (
    DeleteSubmissionsView, FormPagesListView, get_submissions_list_view)

app_name = 'wagtailforms'
urlpatterns = [
    url(r'^$', FormPagesListView.as_view(), name='index'),
    url(r'^submissions/(?P<page_id>\d+)/$', get_submissions_list_view, name='list_submissions'),
    url(r'^submissions/(?P<page_id>\d+)/delete/$', DeleteSubmissionsView.as_view(), name='delete_submissions')
]
