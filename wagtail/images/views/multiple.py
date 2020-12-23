import os.path

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic.base import View

from wagtail.admin.views.generic.multiple_upload import AddView as BaseAddView
from wagtail.admin.views.generic.multiple_upload import DeleteView as BaseDeleteView
from wagtail.admin.views.generic.multiple_upload import EditView as BaseEditView
from wagtail.images import get_image_model
from wagtail.images.fields import ALLOWED_EXTENSIONS
from wagtail.images.forms import get_image_form, get_image_multi_form
from wagtail.images.models import UploadedImage
from wagtail.images.permissions import permission_policy
from wagtail.search.backends import get_search_backends


class AddView(BaseAddView):
    permission_policy = permission_policy
    template_name = 'wagtailimages/multiple/add.html'
    upload_model = UploadedImage

    edit_object_url_name = 'wagtailimages:edit_multiple'
    delete_object_url_name = 'wagtailimages:delete_multiple'
    edit_object_form_prefix = 'image'
    context_object_name = 'image'
    context_object_id_name = 'image_id'

    edit_upload_url_name = 'wagtailimages:create_multiple_from_uploaded_image'
    delete_upload_url_name = 'wagtailimages:delete_upload_multiple'
    edit_upload_form_prefix = 'uploaded-image'
    context_upload_name = 'uploaded_image'
    context_upload_id_name = 'uploaded_image_id'

    def get_model(self):
        return get_image_model()

    def get_upload_form_class(self):
        return get_image_form(self.model)

    def get_edit_form_class(self):
        return get_image_multi_form(self.model)

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

        context.update({
            'max_filesize': self.form.fields['file'].max_upload_size,
            'allowed_extensions': ALLOWED_EXTENSIONS,
            'error_max_file_size': self.form.fields['file'].error_messages['file_too_large_unknown_size'],
            'error_accepted_file_types': self.form.fields['file'].error_messages['invalid_image_extension'],
        })

        return context


class EditView(BaseEditView):
    permission_policy = permission_policy
    pk_url_kwarg = 'image_id'
    edit_object_form_prefix = 'image'
    context_object_name = 'image'
    context_object_id_name = 'image_id'
    edit_object_url_name = 'wagtailimages:edit_multiple'
    delete_object_url_name = 'wagtailimages:delete_multiple'

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
    pk_url_kwarg = 'image_id'
    context_object_id_name = 'image_id'

    def get_model(self):
        return get_image_model()


class CreateFromUploadedImageView(View):
    http_method_names = ['post']
    edit_form_template_name = 'wagtailadmin/generic/multiple_upload/edit_form.html'
    edit_upload_url_name = 'wagtailimages:create_multiple_from_uploaded_image'
    delete_upload_url_name = 'wagtailimages:delete_upload_multiple'
    upload_model = UploadedImage
    upload_pk_url_kwarg = 'uploaded_image_id'
    edit_upload_form_prefix = 'uploaded-image'
    context_object_id_name = 'image_id'
    context_upload_name = 'uploaded_image'

    def get_model(self):
        return get_image_model()

    def get_edit_form_class(self):
        return get_image_multi_form(self.model)

    def save_object(self, form):
        # assign the file content from uploaded_image to the image object, to ensure it gets saved to
        # Image's storage

        self.object.file.save(os.path.basename(self.upload.file.name), self.upload.file.file, save=False)
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

    def post(self, request, *args, **kwargs):
        upload_id = kwargs[self.upload_pk_url_kwarg]
        self.model = self.get_model()
        self.form_class = self.get_edit_form_class()

        self.upload = get_object_or_404(self.upload_model, id=upload_id)

        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if self.upload.uploaded_by_user != request.user:
            raise PermissionDenied

        self.object = self.model()
        form = self.form_class(
            request.POST, request.FILES,
            instance=self.object,
            prefix='%s-%d' % (self.edit_upload_form_prefix, upload_id),
            user=request.user
        )

        if form.is_valid():
            self.save_object(form)
            self.upload.file.delete()
            self.upload.delete()

            return JsonResponse({
                'success': True,
                self.context_object_id_name: self.object.id,
            })
        else:
            return JsonResponse({
                'success': False,
                'form': render_to_string(self.edit_form_template_name, {
                    self.context_upload_name: self.upload,
                    'edit_action': reverse(self.edit_upload_url_name, args=(self.upload.id,)),
                    'delete_action': reverse(self.delete_upload_url_name, args=(self.upload.id,)),
                    'form': form,
                }, request=request),
            })


class DeleteUploadView(View):
    http_method_names = ['post']

    def post(self, request, uploaded_image_id):
        uploaded_image = get_object_or_404(UploadedImage, id=uploaded_image_id)

        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if uploaded_image.uploaded_by_user != request.user:
            raise PermissionDenied

        uploaded_image.file.delete()
        uploaded_image.delete()

        return JsonResponse({
            'success': True,
        })
