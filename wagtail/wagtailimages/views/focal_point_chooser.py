import json

from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import permission_required

from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailadmin.forms import SearchForm

from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtailimages.forms import get_image_form, ImageInsertionForm
from wagtail.wagtailimages.formats import get_image_format


@permission_required('wagtailadmin.access_admin')
def chooser(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    return render_modal_workflow(request, 'wagtailimages/focal_point_chooser/chooser.html', 'wagtailimages/focal_point_chooser/chooser.js', {
        'image': image,
    })
