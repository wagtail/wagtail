from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtailimages import image_processor


def serve(request, image_id, filter_spec):
    image = get_object_or_404(get_image_model(), id=image_id)

    return image_processor.process_image(image.file.file, HttpResponse(content_type='image/jpeg'), filter_spec)
