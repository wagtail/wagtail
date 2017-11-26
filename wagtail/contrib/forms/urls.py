from django.conf.urls import url

from wagtail.contrib.forms import views

app_name = 'wagtailforms'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^submissions/(\d+)/$', views.list_submissions, name='list_submissions'),
    url(r'^submissions/(\d+)/delete/$', views.delete_submissions, name='delete_submissions')
]
