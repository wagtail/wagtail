from django.conf.urls import url
from wagtail.wagtailusers.views import users

urlpatterns = [
    url(r'^$', users.index, name='wagtailusers_index'),
    url(r'^new/$', users.create, name='wagtailusers_create'),
    url(r'^(\d+)/$', users.edit, name='wagtailusers_edit'),
]
