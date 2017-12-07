from django.conf.urls import url

from wagtail.contrib.forms import views

app_name = 'wagtailforms'
urlpatterns = [
    url(r'^$', views.ListFormPagesView.as_view(), name='index'),
    url(r'^submissions/(?P<page_id>\d+)/$', views.get_list_submissions_view, name='list_submissions'),
    url(r'^submissions/(?P<page_id>\d+)/delete/$', views.DeleteSubmissionsView.as_view(), name='delete_submissions')
]
