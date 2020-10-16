from django.urls import path

from wagtail.contrib.forms.views import (
    DeleteSubmissionsView, FormPagesListView, get_submissions_list_view)


app_name = 'wagtailforms'
urlpatterns = [
    path('', FormPagesListView.as_view(), name='index'),
    path('submissions/<int:page_id>/', get_submissions_list_view, name='list_submissions'),
    path('submissions/<int:page_id>/delete/', DeleteSubmissionsView.as_view(), name='delete_submissions')
]
