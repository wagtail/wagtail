import json

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import permission_required
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
from django.views.decorators.vary import vary_on_headers
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.encoding import force_text

from wagtail.wagtailsearch.backends import get_search_backends

from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtailimages.forms import get_image_form
from wagtail.wagtailimages.fields import ALLOWED_EXTENSIONS
from wagtail.utils.compat import render_to_string


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


@permission_required('wagtailimages.add_image')
@vary_on_headers('X-Requested-With')
def add(request):
    Image = get_image_model()
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
                }, request=request),
            })
        else:
            # Validation error
            return json_response({
                'success': False,

                # https://github.com/django/django/blob/stable/1.6.x/django/forms/util.py#L45
                'error_message': '\n'.join(['\n'.join([force_text(i) for i in v]) for k, v in form.errors.items()]),
            })
    else:
        form = ImageForm()

    return render(request, 'wagtailimages/multiple/add.html', {
        'max_filesize': form.fields['file'].max_upload_size,
        'help_text': form.fields['file'].help_text,
        'allowed_extensions': ALLOWED_EXTENSIONS,
        'error_max_file_size': form.fields['file'].error_messages['file_too_large_unknown_size'],
        'error_accepted_file_types': form.fields['file'].error_messages['invalid_image'],
    })


@require_POST
def edit(request, image_id, callback=None):
    Image = get_image_model()
    ImageForm = get_image_edit_form(Image)

    image = get_object_or_404(Image, id=image_id)

    if not request.is_ajax():
        return HttpResponseBadRequest("Cannot POST to this view without AJAX")

    if not image.is_editable_by_user(request.user):
        raise PermissionDenied

    form = ImageForm(request.POST, request.FILES, instance=image, prefix='image-' + image_id)

    if form.is_valid():
        form.save()

        # Reindex the image to make sure all tags are indexed
        for backend in get_search_backends():
            backend.add(image)

        return json_response({
            'success': True,
            'image_id': int(image_id),
        })
    else:
        return json_response({
            'success': False,
            'image_id': int(image_id),
            'form': render_to_string('wagtailimages/multiple/edit_form.html', {
                'image': image,
                'form': form,
            }, request=request),
        })


@require_POST
def delete(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    if not request.is_ajax():
        return HttpResponseBadRequest("Cannot POST to this view without AJAX")

    if not image.is_editable_by_user(request.user):
        raise PermissionDenied

    image.delete()

    return json_response({
        'success': True,
        'image_id': int(image_id),
    })
