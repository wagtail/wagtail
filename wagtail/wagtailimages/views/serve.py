from __future__ import absolute_import, unicode_literals

import base64
import hashlib
import hmac
import imghdr
from wsgiref.util import FileWrapper

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import HttpResponse, HttpResponsePermanentRedirect, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils.six import text_type
from django.views.generic import View

from wagtail.wagtailimages.exceptions import InvalidFilterSpecError
from wagtail.wagtailimages.models import SourceImageIOError, get_image_model


def generate_signature(image_id, filter_spec, key=None):
    if key is None:
        key = settings.SECRET_KEY

    # Key must be a bytes object
    if isinstance(key, text_type):
        key = key.encode()

    # Based on libthumbor hmac generation
    # https://github.com/thumbor/libthumbor/blob/b19dc58cf84787e08c8e397ab322e86268bb4345/libthumbor/crypto.py#L50
    url = '{}/{}/'.format(image_id, filter_spec)
    return base64.urlsafe_b64encode(hmac.new(key, url.encode(), hashlib.sha1).digest())


def verify_signature(signature, image_id, filter_spec, key=None):
    return signature == generate_signature(image_id, filter_spec, key=key)


class ServeView(View):
    model = get_image_model()
    action = 'serve'
    key = None

    def get(self, request, signature, image_id, filter_spec):
        if not verify_signature(signature.encode(), image_id, filter_spec, key=self.key):
            raise PermissionDenied

        image = get_object_or_404(self.model, id=image_id)

        # Get/generate the rendition
        try:
            rendition = image.get_rendition(filter_spec)
        except SourceImageIOError:
            return HttpResponse("Source image file not found", content_type='text/plain', status=410)
        except InvalidFilterSpecError:
            return HttpResponse("Invalid filter spec: " + filter_spec, content_type='text/plain', status=400)

        # Serve it
        if self.action == 'serve':
            # Open and serve the file
            rendition.file.open('rb')
            image_format = imghdr.what(rendition.file)
            return StreamingHttpResponse(FileWrapper(rendition.file), content_type='image/' + image_format)
        elif self.action == 'redirect':
            # Redirect to the file's public location
            return HttpResponsePermanentRedirect(rendition.url)
        else:
            raise ImproperlyConfigured("ServeView action must be either 'serve' or 'redirect'")


serve = ServeView.as_view()
