from django.urls import path, re_path

from wagtail.documents.views import chooser, documents, multiple

app_name = 'wagtaildocs'
urlpatterns = [
    path('', documents.index, name='index'),
    path('add/', documents.add, name='add'),
    re_path(r'^edit/(\d+)/$', documents.edit, name='edit'),
    re_path(r'^delete/(\d+)/$', documents.delete, name='delete'),

    path('multiple/add/', multiple.add, name='add_multiple'),
    re_path(r'^multiple/(\d+)/$', multiple.edit, name='edit_multiple'),
    re_path(r'^multiple/(\d+)/delete/$', multiple.delete, name='delete_multiple'),

    path('chooser/', chooser.chooser, name='chooser'),
    re_path(r'^chooser/(\d+)/$', chooser.document_chosen, name='document_chosen'),
    path('chooser/upload/', chooser.chooser_upload, name='chooser_upload'),
    re_path(r'^usage/(\d+)/$', documents.usage, name='document_usage'),
]
