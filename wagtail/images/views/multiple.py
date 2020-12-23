import os.path

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic.base import View

from wagtail.admin.views.generic.multiple_upload import AddView as BaseAddView
from wagtail.images import get_image_model
from wagtail.images.fields import ALLOWED_EXTENSIONS
from wagtail.images.forms import get_image_form, get_image_multi_form
from wagtail.images.models import UploadedImage
from wagtail.images.permissions import permission_policy
from wagtail.search.backends import get_search_backends


class AddView(BaseAddView):
    permission_policy = permission_policy
    template_name = 'wagtailimages/multiple/add.html'
    edit_form_template_name = 'wagtailimages/multiple/edit_form.html'
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


class EditView(View):
    http_method_names = ['post']
    permission_policy = permission_policy

    def get_model(self):
        return get_image_model()

    def get_edit_form_class(self):
        return get_image_multi_form(self.model)

    def post(self, request, image_id, callback=None):
        self.model = self.get_model()
        self.form_class = self.get_edit_form_class()

        image = get_object_or_404(self.model, id=image_id)

        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if not self.permission_policy.user_has_permission_for_instance(request.user, 'change', image):
            raise PermissionDenied

        form = self.form_class(
            request.POST, request.FILES, instance=image, prefix='image-%d' % image_id, user=request.user
        )

        if form.is_valid():
            form.save()

            # Reindex the image to make sure all tags are indexed
            for backend in get_search_backends():
                backend.add(image)

            return JsonResponse({
                'success': True,
                'image_id': int(image_id),
            })
        else:
            return JsonResponse({
                'success': False,
                'image_id': int(image_id),
                'form': render_to_string('wagtailimages/multiple/edit_form.html', {
                    'image': image,
                    'edit_action': reverse('wagtailimages:edit_multiple', args=(image_id,)),
                    'delete_action': reverse('wagtailimages:delete_multiple', args=(image_id,)),
                    'form': form,
                }, request=request),
            })


class DeleteView(View):
    http_method_names = ['post']
    permission_policy = permission_policy

    def get_model(self):
        return get_image_model()

    def post(self, request, image_id):
        self.model = self.get_model()
        image = get_object_or_404(self.model, id=image_id)

        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if not self.permission_policy.user_has_permission_for_instance(request.user, 'delete', image):
            raise PermissionDenied

        image.delete()

        return JsonResponse({
            'success': True,
            'image_id': int(image_id),
        })


class CreateFromUploadedImageView(View):
    http_method_names = ['post']

    def get_model(self):
        return get_image_model()

    def get_edit_form_class(self):
        return get_image_multi_form(self.model)

    def post(self, request, uploaded_image_id):
        self.model = self.get_model()
        self.form_class = self.get_edit_form_class()

        uploaded_image = get_object_or_404(UploadedImage, id=uploaded_image_id)

        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if uploaded_image.uploaded_by_user != request.user:
            raise PermissionDenied

        image = self.model()
        form = self.form_class(
            request.POST, request.FILES, instance=image, prefix='uploaded-image-%d' % uploaded_image_id, user=request.user
        )

        if form.is_valid():
            # assign the file content from uploaded_image to the image object, to ensure it gets saved to
            # Image's storage

            image.file.save(os.path.basename(uploaded_image.file.name), uploaded_image.file.file, save=False)
            image.uploaded_by_user = request.user
            image.file_size = image.file.size
            image.file.open()
            image.file.seek(0)
            image._set_file_hash(image.file.read())
            image.file.seek(0)
            form.save()

            uploaded_image.file.delete()
            uploaded_image.delete()

            # Reindex the image to make sure all tags are indexed
            for backend in get_search_backends():
                backend.add(image)

            return JsonResponse({
                'success': True,
                'image_id': image.id,
            })
        else:
            return JsonResponse({
                'success': False,
                'form': render_to_string('wagtailimages/multiple/edit_form.html', {
                    'uploaded_image': uploaded_image,
                    'edit_action': reverse('wagtailimages:create_multiple_from_uploaded_image', args=(uploaded_image.id,)),
                    'delete_action': reverse('wagtailimages:delete_upload_multiple', args=(uploaded_image.id,)),
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
