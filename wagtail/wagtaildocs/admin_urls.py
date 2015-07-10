from django.conf.urls import url
from wagtail.wagtaildocs.views import documents, chooser


urlpatterns = [
    url(r'^$', documents.index, name='index'),
    url(r'^add/$', documents.add, name='add'),
    url(r'^edit/(\d+)/$', documents.edit, name='edit_document'),
    url(r'^delete/(\d+)/$', documents.delete, name='delete_document'),

    url(r'^chooser/$', chooser.chooser, name='chooser'),
    url(r'^chooser/(\d+)/$', chooser.document_chosen, name='document_chosen'),
    url(r'^chooser/upload/$', chooser.chooser_upload, name='chooser_upload'),
    url(r'^usage/(\d+)/$', documents.usage, name='document_usage'),
]
