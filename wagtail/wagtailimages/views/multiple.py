from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers


from django.forms.models import modelformset_factory
from django.template.loader import render_to_string
from django.http import HttpResponse

from wagtail.wagtailadmin.forms import SearchForm

from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtailimages.forms import get_image_form_for_multi

import json

@permission_required('wagtailimages.add_image')
@vary_on_headers('X-Requested-With')
def add(request):
    ImageForm = get_image_form_for_multi()
    ImageModel = get_image_model()

    if request.POST and request.is_ajax():
        if not request.FILES:
            return HttpResponseBadRequest('Must upload a file')
        else:
            image = ImageModel(uploaded_by_user=request.user,  title=request.FILES['files[]'].name, file=request.FILES['files[]'])
            image.save()
            form = ImageForm(instance=image, prefix='image-%d'%image.id)

            return render(request, 'wagtailimages/multiple/edit.html', {
                'image': image,
                'form': form
            })
    else:
        pass

    return render(request, "wagtailimages/multiple/add.html", {})

@permission_required('wagtailadmin.access_admin')  # more specific permission tests are applied within the view
def edit(request, image_id, callback=None):
    Image = get_image_model()
    ImageForm = get_image_form_for_multi()

    image = get_object_or_404(Image, id=image_id)

    if not image.is_editable_by_user(request.user):
        raise PermissionDenied

    if request.POST:
        form = ImageForm(request.POST, request.FILES, instance=image, prefix='image-'+image_id)
        if form.is_valid():
            form.save()
            return HttpResponse(render_to_string("wagtailimages/multiple/confirmation.json", {
                'success': True,
                'image_id': image_id
                }))
        else:
            pass

    return HttpResponse(render_to_string("wagtailimages/multiple/confirmation.json", {
        'success': False,
        'image_id': image_id
        }))

@permission_required('wagtailadmin.access_admin')  # more specific permission tests are applied within the view
def delete(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    if not image.is_editable_by_user(request.user):
        raise PermissionDenied

    if request.POST:
        image.delete()
        return HttpResponse(render_to_string("wagtailimages/multiple/confirmation.json", {
            'success': True,
            'image_id': image_id
            }))
    else:
        return HttpResponse(render_to_string("wagtailimages/multiple/confirmation.json", {
            'success': False,
            'image_id': image_id
            }))