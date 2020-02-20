from django.urls import path, re_path

from wagtail.admin.views import collection_privacy, collections

app_name = 'wagtailadmin_collections'
urlpatterns = [
    path('', collections.Index.as_view(), name='index'),
    path('add/', collections.Create.as_view(), name='add'),
    path('<int:pk>/', collections.Edit.as_view(), name='edit'),
    # TODO: replace this with path converter
    re_path(r'^(\d+)/delete/$', collections.Delete.as_view(), name='delete'),
    path('<int:collection_id>/privacy/', collection_privacy.set_privacy, name='set_privacy'),
]
