from typing import TYPE_CHECKING, Optional

from django.core.exceptions import ImproperlyConfigured
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.cache import patch_cache_control
from django.utils.decorators import classonlymethod
from django.views.generic import View

from wagtail.images import get_image_model
from wagtail.images.exceptions import InvalidFilterSpecError
from wagtail.images.models import SourceImageIOError
from wagtail.images.utils import generate_signature, verify_signature
from wagtail.utils.sendfile import sendfile

if TYPE_CHECKING:
    from django.http import HttpRequest
    from django.http.response import HttpResponseBase, HttpResponseRedirectBase

    from wagtail.images.models import AbstractImage, AbstractRendition


def generate_image_url(image, filter_spec, viewname="wagtailimages_serve", key=None):
    signature = generate_signature(image.id, filter_spec, key)
    url = reverse(viewname, args=(signature, image.id, filter_spec))
    url += image.file.name[len("original_images/") :]
    return url


class ServeView(View):
    model = get_image_model()
    action = "serve"
    key = None

    serve_cache_control_headers = {
        "max_age": 3600,
        "s_maxage": 3600,
        "public": True,
    }
    error_cache_control_headers = {
        "max_age": 3600,
        "s_maxage": 3600,
        "public": True,
    }
    redirect_cache_control_headers = {
        "max_age": 3600,
        "s_maxage": 3600,
        "public": True,
    }

    @classonlymethod
    def as_view(cls, **initkwargs):
        if "action" in initkwargs:
            if initkwargs["action"] not in ["serve", "redirect"]:
                raise ImproperlyConfigured(
                    "ServeView action must be either 'serve' or 'redirect'"
                )

        return super().as_view(**initkwargs)

    def get(
        self,
        request: "HttpRequest",
        signature: str,
        image_id: int,
        filter_spec: str,
        filename: Optional[str] = None,
    ):
        if not verify_signature(
            signature.encode(), image_id, filter_spec, key=self.key
        ):
            return self.get_error_response("Invalid signature", 400)

        image = self.get_image(image_id)

        # Get/generate the rendition
        try:
            rendition = image.get_rendition(filter_spec)
        except SourceImageIOError:
            return self.get_error_response("Source image file not found", 410)
        except InvalidFilterSpecError:
            return self.get_error_response(f"Invalid filter spec: {filter_spec}", 400)
        # Make the image object available without an additional query
        rendition.image = image

        return self.get_success_response(rendition)

    def get_image(self, image_id: int) -> "AbstractImage":
        return get_object_or_404(self.model, id=image_id)

    def get_success_response(
        self, rendition: "AbstractRendition"
    ) -> "HttpResponseBase":
        return getattr(self, self.action)(rendition)

    def get_error_response(self, message: str, status_code: int) -> HttpResponse:
        response = HttpResponse(message, content_type="text/plain", status=status_code)
        if self.error_cache_control_headers:
            patch_cache_control(response, **self.error_cache_control_headers)
        return response

    def serve(self, rendition: "AbstractRendition") -> "FileResponse":
        with rendition.get_willow_image() as willow_image:
            mime_type = willow_image.mime_type

        # Serve the file
        rendition.file.open("rb")
        response = FileResponse(rendition.file, content_type=mime_type)

        # Add a CSP header to prevent inline execution
        response["Content-Security-Policy"] = "default-src 'none'"

        # Prevent browsers from auto-detecting the content-type of a document
        response["X-Content-Type-Options"] = "nosniff"

        if self.serve_cache_control_headers:
            patch_cache_control(response, **self.serve_cache_control_headers)
        return response

    def redirect(self, rendition: "AbstractRendition") -> "HttpResponseRedirectBase":
        # Redirect to the file's public location
        response = redirect(rendition.url)
        if self.redirect_cache_control_headers:
            patch_cache_control(response, **self.redirect_cache_control_headers)
        return response


serve = ServeView.as_view()


class SendFileView(ServeView):
    backend = None

    def serve(self, rendition):
        response = sendfile(self.request, rendition.file.path, backend=self.backend)

        # Add a CSP header to prevent inline execution
        response["Content-Security-Policy"] = "default-src 'none'"

        # Prevent browsers from auto-detecting the content-type of a document
        response["X-Content-Type-Options"] = "nosniff"

        if self.serve_cache_control_headers:
            patch_cache_control(response, **self.serve_cache_control_headers)

        return response
