import os.path

import requests
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy

from wagtail.admin.views.generic.base import WagtailAdminTemplateMixin
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
from wagtail.images.forms import get_image_form, get_image_multi_form
from wagtail.images.models import logger
from wagtail.images.permissions import ImagesPermissionPolicyGetter, permission_policy
from wagtail.images.utils import (
    find_image_duplicates,
    get_accept_attributes,
    get_allowed_image_extensions,
)


class AddView(WagtailAdminTemplateMixin, BaseAddView):
    permission_policy = ImagesPermissionPolicyGetter()
    template_name = "wagtailimages/multiple/add.html"
    header_icon = "image"
    page_title = gettext_lazy("Add images")

    index_url_name = "wagtailimages:index"
    edit_object_url_name = "wagtailimages:edit_multiple"
    delete_object_url_name = "wagtailimages:delete_multiple"
    edit_object_form_prefix = "image"
    context_object_name = "image"
    context_object_id_name = "image_id"

    edit_upload_url_name = "wagtailimages:create_multiple_from_uploaded_image"
    delete_upload_url_name = "wagtailimages:delete_upload_multiple"
    edit_upload_form_prefix = "uploaded-image"
    context_upload_name = "uploaded_image"
    context_upload_id_name = "uploaded_file_id"

    def get_breadcrumbs_items(self):
        return self.breadcrumbs_items + [
            {
                "url": reverse(self.index_url_name),
                "label": capfirst(self.model._meta.verbose_name_plural),
            },
            {"url": "", "label": self.get_page_title()},
        ]

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
        image.save()
        return image

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "max_filesize": self.form.fields["file"].max_upload_size,
                "max_title_length": self.form.fields["title"].max_length,
                "allowed_extensions": get_allowed_image_extensions(),
                "accept_attributes": get_accept_attributes(),
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


class DeleteView(BaseDeleteView):
    permission_policy = permission_policy
    pk_url_kwarg = "image_id"
    context_object_id_name = "image_id"

    def get_model(self):
        return get_image_model()


class CreateFromUploadedImageView(BaseCreateFromUploadView):
    edit_upload_url_name = "wagtailimages:create_multiple_from_uploaded_image"
    delete_upload_url_name = "wagtailimages:delete_upload_multiple"
    upload_pk_url_kwarg = "uploaded_file_id"
    edit_upload_form_prefix = "uploaded-image"
    context_object_id_name = "image_id"
    context_upload_name = "uploaded_image"

    def get_model(self):
        return get_image_model()

    def get_edit_form_class(self):
        return get_image_multi_form(self.model)

    def save_object(self, form):
        # assign the file content from uploaded_image to the image object to ensure it gets saved to
        # Image's storage

        self.object.file.save(
            os.path.basename(self.upload.file.name), self.upload.file.file, save=False
        )
        self.object.uploaded_by_user = self.request.user

        # form.save() would normally handle writing the image file metadata, but in this case the
        # file handling happens outside the form, so we need to do that manually
        self.object._set_image_file_metadata()

        form.save()


class DeleteUploadView(BaseDeleteUploadView):
    upload_pk_url_kwarg = "uploaded_file_id"

    def get_model(self):
        return get_image_model()


ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/bmp",
    "image/webp",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class AddFromURLView(AddView):
    """
    AJAX view for bulk image upload from URLs.

    This view handles POST requests containing image URLs and creates
    Wagtail Image objects. It extends Wagtail's AddView to leverage
    built-in duplicate detection and form validation.
    """

    template_name = "wagtailimages/images/add_from_url.html"

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and header to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs_items"] = [
            {"url": "", "label": gettext_lazy("Add from URL")},
        ]
        context["header_title"] = gettext_lazy("Add image from URL")
        return context

    def post(self, request):
        """
        Handle image upload from URL.

        Args:
            request: The HTTP request containing 'url' and optional 'collection'

        Returns:
            JsonResponse with success/error status and image data
        """
        image_url = request.POST.get("url")

        if not image_url:
            return JsonResponse(
                {
                    "success": False,
                    "error_message": gettext_lazy("Please provide a URL."),
                }
            )

        try:
            # Download the image data
            logger.info(f"Downloading image from: {image_url}")
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            # Validate content type
            content_type = (
                response.headers.get("Content-Type", "").split(";")[0].strip().lower()
            )
            if content_type not in ALLOWED_CONTENT_TYPES:
                logger.warning(f"Invalid content type for {image_url}: {content_type}")
                return JsonResponse(
                    {
                        "success": False,
                        "error_message": gettext_lazy(
                            "Invalid file type. Allowed types: JPEG, PNG, GIF, BMP, WEBP."
                        ),
                    }
                )

            # Validate file size
            file_size = len(response.content)
            if file_size > MAX_FILE_SIZE:
                logger.warning(f"File too large for {image_url}: {file_size} bytes")
                return JsonResponse(
                    {
                        "success": False,
                        "error_message": gettext_lazy(
                            "File size exceeds maximum allowed size of {size} MB."
                        ).format(size=MAX_FILE_SIZE // (1024 * 1024)),
                    }
                )

            if file_size == 0:
                logger.warning(f"Empty file downloaded from {image_url}")
                return JsonResponse(
                    {
                        "success": False,
                        "error_message": gettext_lazy("The downloaded file is empty."),
                    }
                )

            # Extract filename from URL, removing query params and fragments
            url_path = image_url.split("?")[0].split("#")[0]
            filename = os.path.basename(url_path)

            # If no filename or no extension, generate one based on the content type
            if not filename or "." not in filename:
                extension_map = {
                    "image/jpeg": ".jpg",
                    "image/jpg": ".jpg",
                    "image/png": ".png",
                    "image/gif": ".gif",
                    "image/bmp": ".bmp",
                    "image/webp": ".webp",
                }
                extension = extension_map.get(content_type, ".jpg")
                filename = f"image{extension}"

            # Sanitize filename and limit length
            filename = filename[:255]  # Max filename length on most filesystems

            # Wrap in Django file object
            file = SimpleUploadedFile(
                name=filename,
                content=response.content,
                content_type=content_type,
            )

            # Use Wagtail's upload form for validation
            upload_form_class = self.get_upload_form_class()
            form = upload_form_class(
                data={
                    "title": os.path.splitext(filename)[0],
                    "collection": request.POST.get("collection", 1),
                },
                files={"file": file},
                user=request.user,
            )

            if form.is_valid():
                # Save using Wagtail's method (includes duplicate checking)
                self.object = self.save_object(form)

                # Get response data (includes duplicate info)
                response_data = self.get_edit_object_response_data()

                # If duplicate detected, remove the newly created object
                if response_data.get("duplicate"):
                    logger.info(f"Duplicate image detected: {image_url}")
                    self.object.delete()
                else:
                    logger.info(f"Image uploaded successfully: {self.object.title}")

                return JsonResponse(response_data)
            else:
                # Return form validation errors
                logger.warning(f"Form validation failed for {image_url}: {form.errors}")
                return JsonResponse(self.get_invalid_response_data(form))

        except requests.exceptions.Timeout:
            logger.error(f"Timeout downloading image from {image_url}")
            return JsonResponse(
                {
                    "success": False,
                    "error_message": gettext_lazy(
                        "Request timeout - the server took too long to respond."
                    ),
                }
            )
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error downloading {image_url}: {e}")
            return JsonResponse(
                {
                    "success": False,
                    "error_message": gettext_lazy("HTTP error: {status}").format(
                        status=e.response.status_code
                    ),
                }
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Download failed for {image_url}: {e}")
            return JsonResponse(
                {
                    "success": False,
                    "error_message": gettext_lazy("Download failed: {error}").format(
                        error=str(e)
                    ),
                }
            )
        except Exception as e:  # noqa: BLE001
            logger.exception(f"Unexpected error processing {image_url}")
            return JsonResponse(
                {
                    "success": False,
                    "error_message": gettext_lazy("Unexpected error: {error}").format(
                        error=str(e)
                    ),
                }
            )
