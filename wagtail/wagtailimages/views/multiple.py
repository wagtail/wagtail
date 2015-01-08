import json

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied, ValidationError
from django.views.decorators.vary import vary_on_headers
from django.http import HttpResponse, HttpResponseBadRequest
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.utils.encoding import force_text
from django.views.generic.base import View

from wagtail.wagtailsearch.backends import get_search_backends

from wagtail.wagtailimages.forms import get_image_form
from wagtail.wagtailimages.fields import (
    MAX_UPLOAD_SIZE,
    IMAGE_FIELD_HELP_TEXT,
    INVALID_IMAGE_ERROR,
    ALLOWED_EXTENSIONS,
    SUPPORTED_FORMATS_TEXT,
    FILE_TOO_LARGE_ERROR,
)

from .images import ImageModuleViewMixin


def json_response(document):
    return HttpResponse(json.dumps(document), content_type='application/json')


def get_image_edit_form(ImageModel):
    ImageForm = get_image_form(ImageModel)

    # Make a new form with the file and focal point fields excluded
    class ImageEditForm(ImageForm):
        class Meta(ImageForm.Meta):
            model = ImageModel
            exclude = (
                'file',
                'focal_point_x',
                'focal_point_y',
                'focal_point_width',
                'focal_point_height',
            )

    return ImageEditForm


class ImageCreateMultipleView(ImageModuleViewMixin, View):
    @method_decorator(permission_required('wagtailimages.add_image'))
    @method_decorator(vary_on_headers('X-Requested-With'))
    def dispatch(self, request):
        Image = self.model
        ImageForm = get_image_form(Image)

        if request.method == 'POST':
            if not request.is_ajax():
                return HttpResponseBadRequest("Cannot POST to this view without AJAX")

            if not request.FILES:
                return HttpResponseBadRequest("Must upload a file")

            # Build a form for validation
            form = ImageForm({
                'title': request.FILES['files[]'].name,
            }, {
                'file': request.FILES['files[]'], 
            })
            
            if form.is_valid():
                # Save it
                image = form.save(commit=False)
                image.uploaded_by_user = request.user
                image.save()

                # Success! Send back an edit form for this image to the user
                return json_response({
                    'success': True,
                    'image_id': int(image.id),
                    'form': render_to_string('wagtailimages/multiple/edit_form.html', {
                        'image': image,
                        'form': get_image_edit_form(Image)(instance=image, prefix='image-%d' % image.id),
                        'view': self,
                        'module': self.module,
                    }, context_instance=RequestContext(request)),
                })
            else:
                # Validation error
                return json_response({
                    'success': False,

                    # https://github.com/django/django/blob/stable/1.6.x/django/forms/util.py#L45
                    'error_message': '\n'.join(['\n'.join([force_text(i) for i in v]) for k, v in form.errors.items()]),
                })

        return render(request, 'wagtailimages/multiple/add.html', {
            'max_filesize': MAX_UPLOAD_SIZE,
            'help_text': IMAGE_FIELD_HELP_TEXT,
            'allowed_extensions': ALLOWED_EXTENSIONS,
            'error_max_file_size': FILE_TOO_LARGE_ERROR,
            'error_accepted_file_types': INVALID_IMAGE_ERROR,
            'view': self,
            'module': self.module,
        })


class ImageCreateMultipleUpdateView(ImageModuleViewMixin, View):
    @method_decorator(permission_required('wagtailadmin.access_admin'))
    def post(self, request, pk, callback=None):
        Image = self.model
        ImageForm = get_image_edit_form(Image)

        image = get_object_or_404(Image, id=pk)

        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if not image.is_editable_by_user(request.user):
            raise PermissionDenied

        form = ImageForm(request.POST, request.FILES, instance=image, prefix='image-'+pk)

        if form.is_valid():
            form.save()

            # Reindex the image to make sure all tags are indexed
            for backend in get_search_backends():
                backend.add(image)

            return json_response({
                'success': True,
                'image_id': int(pk),
            })
        else:
            return json_response({
                'success': False,
                'image_id': int(pk),
                'form': render_to_string('wagtailimages/multiple/edit_form.html', {
                    'image': image,
                    'form': form,
                    'view': self,
                    'module': self.module,
                }, context_instance=RequestContext(request)),
            })


class ImageCreateMultipleDeleteView(ImageModuleViewMixin, View):
    @method_decorator(permission_required('wagtailadmin.access_admin'))
    def post(self, request, pk):
        image = get_object_or_404(self.model, id=pk)

        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if not image.is_editable_by_user(request.user):
            raise PermissionDenied

        image.delete()

        return json_response({
            'success': True,
            'image_id': int(pk),
        })
