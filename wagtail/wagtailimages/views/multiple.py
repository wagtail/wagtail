import json

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.vary import vary_on_headers
from django.http import HttpResponseBadRequest

from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtailimages.forms import get_image_form_for_multi


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

        image = Image(uploaded_by_user=request.user,  title=request.FILES['files[]'].name, file=request.FILES['files[]'])
        image.save()
        form = ImageForm(instance=image, prefix='image-%d'%image.id)

        return render(request, 'wagtailimages/multiple/edit_form.html', {
            'image': image,
            'form': form
        })

    return render(request, 'wagtailimages/multiple/add.html', {})


@permission_required('wagtailadmin.access_admin')  # more specific permission tests are applied within the view
def edit(request, image_id, callback=None):
    Image = get_image_model()
    ImageForm = get_image_form_for_multi()

    image = get_object_or_404(Image, id=image_id)

    if not image.is_editable_by_user(request.user):
        raise PermissionDenied

    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES, instance=image, prefix='image-'+image_id)
        if form.is_valid():
            form.save()
            return render(request, 'wagtailimages/multiple/confirmation.json', {
                'success': True,
                'image': image,
            }, content_type='application/json')

    return render(request, 'wagtailimages/multiple/confirmation.json', {
        'success': False,
        'image': image,
        'form': form,
    }, content_type='application/json')


@permission_required('wagtailadmin.access_admin')  # more specific permission tests are applied within the view
def delete(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    if not image.is_editable_by_user(request.user):
        raise PermissionDenied

    if request.method == 'POST':
        image.delete()
        return render(request, 'wagtailimages/multiple/confirmation.json', {
            'success': True,
            'image': image,
        }, content_type='application/json')
    else:
        return render(request, 'wagtailimages/multiple/confirmation.json', {
            'success': False,
            'image': image,
        }, content_type='application/json')
