from django.conf.urls import url
from wagtail.wagtailusers.views import users

urlpatterns = [
    url(r'^$', users.index, name='wagtailusers_users_index'),
    url(r'^new/$', users.create, name='wagtailusers_users_create'),
    url(r'^([^\/]+)/$', users.edit, name='wagtailusers_users_edit'),
]
