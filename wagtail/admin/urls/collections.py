from django.conf.urls import url

from wagtail.admin.views import collection_privacy, collections

app_name = 'wagtailadmin_collections'
urlpatterns = [
    url(r'^$', collections.Index.as_view(), name='index'),
    url(r'^(\d+)/$', collections.Index.as_view(), name='parent_index'),
    url(r'^(\d+)/add/$', collections.Create.as_view(), name='add_child'),
    url(r'^(\d+)/edit/$', collections.Edit.as_view(), name='edit'),
    url(r'^(\d+)/delete/$', collections.Delete.as_view(), name='delete'),
    url(r'^(\d+)/privacy/$', collection_privacy.set_privacy, name='set_privacy'),
]
