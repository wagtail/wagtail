import imghdr
from wsgiref.util import FileWrapper

from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import (
    HttpResponse,
    HttpResponsePermanentRedirect,
    StreamingHttpResponse,
)
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import classonlymethod
from django.views.generic import View

from wagtail.images import get_image_model
from wagtail.images.exceptions import InvalidFilterSpecError
from wagtail.images.models import SourceImageIOError
from wagtail.images.utils import generate_signature, verify_signature
from wagtail.utils.sendfile import sendfile


def generate_image_url(image, filter_spec, viewname="wagtailimages_serve", key=None):
    signature = generate_signature(image.id, filter_spec, key)
    url = reverse(viewname, args=(signature, image.id, filter_spec))
    url += image.file.name[len("original_images/") :]
    return url


class ServeView(View):
    model = get_image_model()
    action = "serve"
    key = None

    @classonlymethod
    def as_view(cls, **initkwargs):
        if "action" in initkwargs:
            if initkwargs["action"] not in ["serve", "redirect"]:
                raise ImproperlyConfigured(
                    "ServeView action must be either 'serve' or 'redirect'"
                )

        return super(ServeView, cls).as_view(**initkwargs)

    def get(self, request, signature, image_id, filter_spec, filename=None):
        if not verify_signature(
            signature.encode(), image_id, filter_spec, key=self.key
        ):
            raise PermissionDenied

        image = get_object_or_404(self.model, id=image_id)

        # Get/generate the rendition
        try:
            rendition = image.get_rendition(filter_spec)
        except SourceImageIOError:
            return HttpResponse(
                "Source image file not found", content_type="text/plain", status=410
            )
        except InvalidFilterSpecError:
            return HttpResponse(
                "Invalid filter spec: " + filter_spec,
                content_type="text/plain",
                status=400,
            )

        return getattr(self, self.action)(rendition)

    def serve(self, rendition):
        # Open and serve the file
        rendition.file.open("rb")
        image_format = imghdr.what(rendition.file)
        return StreamingHttpResponse(
            FileWrapper(rendition.file), content_type="image/" + image_format
        )

    def redirect(self, rendition):
        # Redirect to the file's public location
        return HttpResponsePermanentRedirect(rendition.url)


serve = ServeView.as_view()


class SendFileView(ServeView):
    backend = None

    def serve(self, rendition):
        return sendfile(self.request, rendition.file.path, backend=self.backend)
