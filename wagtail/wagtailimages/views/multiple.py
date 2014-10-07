import json

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import permission_required
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied, ValidationError
from django.views.decorators.vary import vary_on_headers
from django.http import HttpResponse, HttpResponseBadRequest
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from wagtail.wagtailsearch.backends import get_search_backends

from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtailimages.forms import get_image_form_for_multi
from wagtail.wagtailimages.utils.validators import validate_image_format, validate_image_filesize


def json_response(document):
    return HttpResponse(json.dumps(document), content_type='application/json')


@permission_required('wagtailimages.add_image')
@vary_on_headers('X-Requested-With')
def add(request):
    Image = get_image_model()
    ImageForm = get_image_form_for_multi()

    if request.method == 'POST':
        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if not request.FILES:
            return HttpResponseBadRequest("Must upload a file")

        # Check that the uploaded file is valid
        try:
            validate_image_format(request.FILES['files[]'])
            validate_image_filesize(request.FILES['files[]'])
        except ValidationError as e:
            return json_response({
                'success': False,
                'error_message': '\n'.join(e.messages),
            })

        # Save it
        image = Image(uploaded_by_user=request.user, title=request.FILES['files[]'].name, file=request.FILES['files[]'])
        image.save()

        # Success! Send back an edit form for this image to the user
        form = ImageForm(instance=image, prefix='image-%d' % image.id)

        return json_response({
            'success': True,
            'image_id': int(image.id),
            'form': render_to_string('wagtailimages/multiple/edit_form.html', {
                'image': image,
                'form': form,
            }, context_instance=RequestContext(request)),
        })


    return render(request, 'wagtailimages/multiple/add.html', {})


@require_POST
@permission_required('wagtailadmin.access_admin')  # more specific permission tests are applied within the view
def edit(request, image_id, callback=None):
    Image = get_image_model()
    ImageForm = get_image_form_for_multi()

    image = get_object_or_404(Image, id=image_id)

    if not request.is_ajax():
        return HttpResponseBadRequest("Cannot POST to this view without AJAX")

    if not image.is_editable_by_user(request.user):
        raise PermissionDenied

    form = ImageForm(request.POST, request.FILES, instance=image, prefix='image-'+image_id)

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
            }, context_instance=RequestContext(request)),
        })


@require_POST
@permission_required('wagtailadmin.access_admin')  # more specific permission tests are applied within the view
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
