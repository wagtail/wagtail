from django.urls import path

from wagtail.images.views import images, multiple

app_name = "wagtailimages"
urlpatterns = [
    path("", images.IndexView.as_view(), name="index"),
    path("results/", images.IndexView.as_view(results_only=True), name="index_results"),
    path("<int:image_id>/", images.EditView.as_view(), name="edit"),
    path("<int:image_id>/delete/", images.DeleteView.as_view(), name="delete"),
    path(
        "<int:image_id>/generate_url/",
        images.URLGeneratorView.as_view(),
        name="url_generator",
    ),
    path(
        "<int:image_id>/generate_url/<str:filter_spec>/",
        images.GenerateURLView.as_view(),
        name="generate_url",
    ),
    path("<int:image_id>/preview/<str:filter_spec>/", images.preview, name="preview"),
    path("add/", images.CreateView.as_view(), name="add"),
    path("usage/<int:image_id>/", images.UsageView.as_view(), name="image_usage"),
    path("multiple/add/", multiple.AddView.as_view(), name="add_multiple"),
    path("multiple/<int:image_id>/", multiple.EditView.as_view(), name="edit_multiple"),
    path(
        "multiple/create_from_uploaded_image/<int:uploaded_file_id>/",
        multiple.CreateFromUploadedImageView.as_view(),
        name="create_multiple_from_uploaded_image",
    ),
    path(
        "multiple/<int:image_id>/delete/",
        multiple.DeleteView.as_view(),
        name="delete_multiple",
    ),
    path(
        "multiple/delete_upload/<int:uploaded_file_id>/",
        multiple.DeleteUploadView.as_view(),
        name="delete_upload_multiple",
    ),
]
