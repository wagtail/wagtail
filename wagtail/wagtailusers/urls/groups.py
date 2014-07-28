from django.conf.urls import url
from wagtail.wagtailusers.views import groups

urlpatterns = [
    url(r'^$', groups.index, name='wagtailusers_groups_index'),
    url(r'^new/$', groups.create, name='wagtailusers_groups_create'),
    url(r'^(\d+)/$', groups.edit, name='wagtailusers_groups_edit'),
]
