from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import permission_required

from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailimages.models import get_image_model


@permission_required('wagtailadmin.access_admin')
def chooser(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    return render_modal_workflow(request, 'wagtailimages/focal_point_chooser/chooser.html', 'wagtailimages/focal_point_chooser/chooser.js', {
        'image': image,
    })
