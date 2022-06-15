import os.path

from django.template.loader import render_to_string
from django.urls import reverse

from wagtail.admin.views.generic.multiple_upload import AddView as BaseAddView
from wagtail.admin.views.generic.multiple_upload import (
    CreateFromUploadView as BaseCreateFromUploadView,
)
from wagtail.admin.views.generic.multiple_upload import (
    DeleteUploadView as BaseDeleteUploadView,
)
from wagtail.admin.views.generic.multiple_upload import DeleteView as BaseDeleteView
from wagtail.admin.views.generic.multiple_upload import EditView as BaseEditView
from wagtail.images import get_image_model
from wagtail.images.fields import ALLOWED_EXTENSIONS
from wagtail.images.forms import get_image_form, get_image_multi_form
from wagtail.images.models import UploadedImage
from wagtail.images.permissions import ImagesPermissionPolicyGetter, permission_policy
from wagtail.images.utils import find_image_duplicates
from wagtail.search.backends import get_search_backends


class AddView(BaseAddView):
    permission_policy = ImagesPermissionPolicyGetter()
    template_name = "wagtailimages/multiple/add.html"
    upload_model = UploadedImage

    edit_object_url_name = "wagtailimages:edit_multiple"
    delete_object_url_name = "wagtailimages:delete_multiple"
    edit_object_form_prefix = "image"
    context_object_name = "image"
    context_object_id_name = "image_id"

    edit_upload_url_name = "wagtailimages:create_multiple_from_uploaded_image"
    delete_upload_url_name = "wagtailimages:delete_upload_multiple"
    edit_upload_form_prefix = "uploaded-image"
    context_upload_name = "uploaded_image"
    context_upload_id_name = "uploaded_image_id"

    def get_model(self):
        return get_image_model()

    def get_upload_form_class(self):
        return get_image_form(self.model)

    def get_edit_form_class(self):
        return get_image_multi_form(self.model)

    def get_confirm_duplicate_upload_response(self, duplicates):
        return render_to_string(
            "wagtailimages/images/confirm_duplicate_upload.html",
            {
                "existing_image": duplicates[0],
                "delete_action": reverse(
                    self.delete_object_url_name, args=(self.object.id,)
                ),
            },
            request=self.request,
        )

    def get_edit_object_response_data(self):
        data = super().get_edit_object_response_data()
        duplicates = find_image_duplicates(
            image=self.object,
            user=self.request.user,
            permission_policy=self.permission_policy,
        )
        if not duplicates:
            data.update(duplicate=False)
        else:
            data.update(
                duplicate=True,
                confirm_duplicate_upload=self.get_confirm_duplicate_upload_response(
                    duplicates
                ),
            )

        return data

    def save_object(self, form):
        image = form.save(commit=False)
        image.uploaded_by_user = self.request.user
        image.file_size = image.file.size
        image.file.seek(0)
        image._set_file_hash(image.file.read())
        image.file.seek(0)
        image.save()
        return image

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "max_filesize": self.form.fields["file"].max_upload_size,
                "max_title_length": self.form.fields["title"].max_length,
                "allowed_extensions": ALLOWED_EXTENSIONS,
                "error_max_file_size": self.form.fields["file"].error_messages[
                    "file_too_large_unknown_size"
                ],
                "error_accepted_file_types": self.form.fields["file"].error_messages[
                    "invalid_image_extension"
                ],
            }
        )

        return context


class EditView(BaseEditView):
    permission_policy = permission_policy
    pk_url_kwarg = "image_id"
    edit_object_form_prefix = "image"
    context_object_name = "image"
    context_object_id_name = "image_id"
    edit_object_url_name = "wagtailimages:edit_multiple"
    delete_object_url_name = "wagtailimages:delete_multiple"

    def get_model(self):
        return get_image_model()

    def get_edit_form_class(self):
        return get_image_multi_form(self.model)

    def save_object(self, form):
        form.save()

        # Reindex the image to make sure all tags are indexed
        for backend in get_search_backends():
            backend.add(self.object)


class DeleteView(BaseDeleteView):
    permission_policy = permission_policy
    pk_url_kwarg = "image_id"
    context_object_id_name = "image_id"

    def get_model(self):
        return get_image_model()


class CreateFromUploadedImageView(BaseCreateFromUploadView):
    edit_upload_url_name = "wagtailimages:create_multiple_from_uploaded_image"
    delete_upload_url_name = "wagtailimages:delete_upload_multiple"
    upload_model = UploadedImage
    upload_pk_url_kwarg = "uploaded_image_id"
    edit_upload_form_prefix = "uploaded-image"
    context_object_id_name = "image_id"
    context_upload_name = "uploaded_image"

    def get_model(self):
        return get_image_model()

    def get_edit_form_class(self):
        return get_image_multi_form(self.model)

    def save_object(self, form):
        # assign the file content from uploaded_image to the image object, to ensure it gets saved to
        # Image's storage

        self.object.file.save(
            os.path.basename(self.upload.file.name), self.upload.file.file, save=False
        )
        self.object.uploaded_by_user = self.request.user
        self.object.file_size = self.object.file.size
        self.object.file.open()
        self.object.file.seek(0)
        self.object._set_file_hash(self.object.file.read())
        self.object.file.seek(0)
        form.save()

        # Reindex the image to make sure all tags are indexed
        for backend in get_search_backends():
            backend.add(self.object)


class DeleteUploadView(BaseDeleteUploadView):
    upload_model = UploadedImage
    upload_pk_url_kwarg = "uploaded_image_id"
