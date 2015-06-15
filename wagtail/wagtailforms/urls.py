from django.conf.urls import url

from wagtail.wagtailforms import views


urlpatterns = [
    url(r'^$', views.index, name='wagtailforms_index'),
    url(r'^submissions/(\d+)/$', views.list_submissions, name='wagtailforms_list_submissions'),
]
