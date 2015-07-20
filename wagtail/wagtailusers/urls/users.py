from django.conf.urls import url
from wagtail.wagtailusers.views import users

urlpatterns = [
    url(r'^$', users.index, name='index'),
    url(r'^new/$', users.create, name='create'),
    url(r'^([^\/]+)/$', users.edit, name='edit'),
]
