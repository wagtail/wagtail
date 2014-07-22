from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.views.decorators.cache import cache_page

from wagtail.wagtailimages.models import get_image_model, Filter
from wagtail.wagtailimages.utils import verify_signature


@cache_page(60 * 60 * 24 * 60) # Cache for 60 days
def serve(request, signature, image_id, filter_spec):
    image = get_object_or_404(get_image_model(), id=image_id)

    if not verify_signature(signature.encode(), image_id, filter_spec):
        raise PermissionDenied

    try:
        return Filter(spec=filter_spec).process_image(image.file.file, HttpResponse(content_type='image/jpeg'))
    except Filter.InvalidFilterSpecError:
        return HttpResponse("Invalid filter spec: " + filter_spec, content_type='text/plain', status=400)
