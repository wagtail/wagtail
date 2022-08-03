from django.urls import path
from django.http import JsonResponse

from wagtail.images.views import chooser, images, multiple
from wagtail.admin.views.generic.multiple_upload import DeleteView as BaseDeleteView

# used as delete_action, when object is already deleted, just to show user delete animation
class DummyDeleteView(BaseDeleteView):
    def post(self, request, *args, **kwargs):
        return JsonResponse({"success": True})
        
        
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
        "multiple/dummy_delete",
        DummyDeleteView.as_view(),
        name="dummy_delete",
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
]
