from django.urls import path

from wagtail.documents.views import documents, multiple

app_name = "wagtaildocs"
urlpatterns = [
    path("", documents.IndexView.as_view(), name="index"),
    path(
        "results/",
        documents.IndexView.as_view(results_only=True),
        name="index_results",
    ),
    path("add/", documents.CreateView.as_view(), name="add"),
    path("edit/<int:document_id>/", documents.EditView.as_view(), name="edit"),
    path("delete/<int:document_id>/", documents.DeleteView.as_view(), name="delete"),
    path("multiple/add/", multiple.AddView.as_view(), name="add_multiple"),
    path("multiple/<int:doc_id>/", multiple.EditView.as_view(), name="edit_multiple"),
    path(
        "multiple/create_from_uploaded_document/<int:uploaded_file_id>/",
        multiple.CreateFromUploadedDocumentView.as_view(),
        name="create_multiple_from_uploaded_document",
    ),
    path(
        "multiple/<int:doc_id>/delete/",
        multiple.DeleteView.as_view(),
        name="delete_multiple",
    ),
    path(
        "multiple/delete_upload/<int:uploaded_file_id>/",
        multiple.DeleteUploadView.as_view(),
        name="delete_upload_multiple",
    ),
    path(
        "usage/<int:document_id>/", documents.UsageView.as_view(), name="document_usage"
    ),
]
