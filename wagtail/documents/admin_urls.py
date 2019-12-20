from django.conf.urls import url

from wagtail.documents.views import chooser, documents, multiple

app_name = 'wagtaildocs'
urlpatterns = [
    url(r'^$', documents.index, name='index'),
    url(r'^add/$', documents.add, name='add'),
    url(r'^edit/(\d+)/$', documents.edit, name='edit'),
    url(r'^delete/(\d+)/$', documents.delete, name='delete'),

    url(r'^multiple/add/$', multiple.add, name='add_multiple'),
    url(r'^multiple/(\d+)/$', multiple.edit, name='edit_multiple'),
    url(r'^multiple/(\d+)/delete/$', multiple.delete, name='delete_multiple'),

    url(r'^chooser/$', chooser.chooser, name='chooser'),
    url(r'^chooser/(\d+)/$', chooser.document_chosen, name='document_chosen'),
    url(r'^chooser/upload/$', chooser.chooser_upload, name='chooser_upload'),
    url(r'^usage/(\d+)/$', documents.usage, name='document_usage'),
]
