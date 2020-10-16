from django.urls import path

from wagtail.documents.views import chooser, documents, multiple


app_name = 'wagtaildocs'
urlpatterns = [
    path('', documents.index, name='index'),
    path('add/', documents.add, name='add'),
    path('edit/<int:document_id>/', documents.edit, name='edit'),
    path('delete/<int:document_id>/', documents.delete, name='delete'),

    path('multiple/add/', multiple.add, name='add_multiple'),
    path('multiple/<int:doc_id>/', multiple.edit, name='edit_multiple'),
    path('multiple/<int:doc_id>/delete/', multiple.delete, name='delete_multiple'),

    path('chooser/', chooser.chooser, name='chooser'),
    path('chooser/<int:document_id>/', chooser.document_chosen, name='document_chosen'),
    path('chooser/upload/', chooser.chooser_upload, name='chooser_upload'),
    path('usage/<int:document_id>/', documents.usage, name='document_usage'),
]
