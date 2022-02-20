from django.urls import path

from wagtail.images.views import chooser, images, multiple

app_name = "wagtailimages"
urlpatterns = [
    path("", images.IndexView.as_view(), name="index"),
    path("results/", images.ListingResultsView.as_view(), name="listing_results"),
    path("<int:image_id>/", images.edit, name="edit"),
    path("<int:image_id>/delete/", images.delete, name="delete"),
    path("<int:image_id>/generate_url/", images.url_generator, name="url_generator"),
    path(
        "<int:image_id>/generate_url/<str:filter_spec>/",
        images.generate_url,
        name="generate_url",
    ),
    path("<int:image_id>/preview/<str:filter_spec>/", images.preview, name="preview"),
    path("add/", images.add, name="add"),
    path("usage/<int:image_id>/", images.usage, name="image_usage"),
    path("multiple/add/", multiple.AddView.as_view(), name="add_multiple"),
    path("multiple/<int:image_id>/", multiple.EditView.as_view(), name="edit_multiple"),
    path(
        "multiple/create_from_uploaded_image/<int:uploaded_image_id>/",
        multiple.CreateFromUploadedImageView.as_view(),
        name="create_multiple_from_uploaded_image",
    ),
    path(
        "multiple/<int:image_id>/delete/",
        multiple.DeleteView.as_view(),
        name="delete_multiple",
    ),
    path(
        "multiple/delete_upload/<int:uploaded_image_id>/",
        multiple.DeleteUploadView.as_view(),
        name="delete_upload_multiple",
    ),
    path("chooser/", chooser.ChooseView.as_view(), name="chooser"),
    path(
        "chooser/results/", chooser.ChooseResultsView.as_view(), name="chooser_results"
    ),
    path("chooser/<int:image_id>/", chooser.image_chosen, name="image_chosen"),
    path("chooser/upload/", chooser.chooser_upload, name="chooser_upload"),
    path(
        "chooser/<int:image_id>/select_format/",
        chooser.chooser_select_format,
        name="chooser_select_format",
    ),
]
