from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import classonlymethod, method_decorator
from django.views.decorators.cache import cache_control
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

        return super().as_view(**initkwargs)

    @method_decorator(cache_control(max_age=3600, public=True))
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
        with rendition.get_willow_image() as willow_image:
            mime_type = willow_image.mime_type

        # Serve the file
        rendition.file.open("rb")
        response = FileResponse(rendition.file, content_type=mime_type)

        # Add a CSP header to prevent inline execution
        response["Content-Security-Policy"] = "default-src 'none'"

        # Prevent browsers from auto-detecting the content-type of a document
        response["X-Content-Type-Options"] = "nosniff"

        return response

    def redirect(self, rendition):
        # Redirect to the file's public location
        return redirect(rendition.url)


serve = ServeView.as_view()


class SendFileView(ServeView):
    backend = None

    def serve(self, rendition):
        response = sendfile(self.request, rendition.file.path, backend=self.backend)

        # Add a CSP header to prevent inline execution
        response["Content-Security-Policy"] = "default-src 'none'"

        # Prevent browsers from auto-detecting the content-type of a document
        response["X-Content-Type-Options"] = "nosniff"

        return response
