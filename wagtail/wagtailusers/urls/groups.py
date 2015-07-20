from django.conf.urls import url
from wagtail.wagtailusers.views import groups

urlpatterns = [
    url(r'^$', groups.index, name='index'),
    url(r'^new/$', groups.create, name='create'),
    url(r'^(\d+)/$', groups.edit, name='edit'),
    url(r'^(\d+)/delete/$', groups.delete, name='delete'),
]
