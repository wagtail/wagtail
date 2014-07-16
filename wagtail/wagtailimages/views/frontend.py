from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied

from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtailimages.utils import InvalidFilterSpecError, verify_signature
from wagtail.wagtailimages import image_processor


def serve(request, signature, image_id, filter_spec):
    image = get_object_or_404(get_image_model(), id=image_id)

    if not verify_signature(signature, image_id, filter_spec):
        raise PermissionDenied

    try:
        return image_processor.process_image(image.file.file, HttpResponse(content_type='image/jpeg'), filter_spec)
    except InvalidFilterSpecError:
        return HttpResponse("Invalid filter spec: " + filter_spec, content_type='text/plain', status=400)
