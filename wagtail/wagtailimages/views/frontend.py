from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.views.decorators.cache import cache_control

from wagtail.wagtailimages.models import get_image_model, Filter
from wagtail.wagtailimages.utils import verify_signature


@cache_control(max_age=60*60*24*60) # Cache for 60 days
def serve(request, signature, image_id, filter_spec):
    image = get_object_or_404(get_image_model(), id=image_id)

    if not verify_signature(signature.encode(), image_id, filter_spec):
        raise PermissionDenied

    # TODO: Raise 400 error on invalid filter
    return Filter(spec=filter_spec).run(image, HttpResponse(content_type='image/jpeg'))
