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


class ServeView(View):
    model = get_image_model()
    action = 'serve'
    key = None

    def get_key(self):
        if self.key is not None:
            return self.key
        else:
            return settings.SECRET_KEY

    def generate_signature(self, image_id, filter_spec):
        key = self.get_key()

        # Key must be a bytes object
        if isinstance(key, text_type):
            key = key.encode()

        # Get primary key of image instance
        if isinstance(image_id, self.model):
            image_id = image_id.id

        # Based on libthumbor hmac generation
        # https://github.com/thumbor/libthumbor/blob/b19dc58cf84787e08c8e397ab322e86268bb4345/libthumbor/crypto.py#L50
        url = str(image_id) + '/' + str(filter_spec) + '/'
        return base64.urlsafe_b64encode(hmac.new(key, url.encode(), hashlib.sha1).digest())

    def verify_signature(self, signature, image_id, filter_spec):
        return signature == self.generate_signature(image_id, filter_spec)

    def get(self, request, signature, image_id, filter_spec):
        image = get_object_or_404(self.model, id=image_id)

        if not self.verify_signature(signature.encode(), image_id, filter_spec):
            raise PermissionDenied

        try:
            # Get/generate the rendition
            try:
                rendition = image.get_rendition(filter_spec)
            except SourceImageIOError:
                return HttpResponse("Source image file not found", content_type='text/plain', status=410)

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
        except InvalidFilterSpecError:
            return HttpResponse("Invalid filter spec: " + filter_spec, content_type='text/plain', status=400)


serve = ServeView.as_view()
