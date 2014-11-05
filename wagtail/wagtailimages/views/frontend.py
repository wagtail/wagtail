from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper
from django.core.exceptions import PermissionDenied

from wagtail.wagtailimages.models import get_image_model, Filter
from wagtail.wagtailimages.utils import verify_signature


def serve(request, signature, image_id, filter_spec):
    image = get_object_or_404(get_image_model(), id=image_id)

    if not verify_signature(signature.encode(), image_id, filter_spec):
        raise PermissionDenied

    try:
        rendition = image.get_rendition(filter_spec)
        rendition.file.open('rb')
        return HttpResponse(FileWrapper(rendition.file), content_type='image/jpeg')
    except Filter.InvalidFilterSpecError:
        return HttpResponse("Invalid filter spec: " + filter_spec, content_type='text/plain', status=400)
