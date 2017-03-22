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
from django.utils.decorators import classonlymethod
from django.utils.six import text_type
from django.views.generic import View

from wagtail.utils.sendfile import sendfile
from wagtail.wagtailimages import get_image_model
from wagtail.wagtailimages.exceptions import InvalidFilterSpecError
from wagtail.wagtailimages.models import SourceImageIOError


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

    @classonlymethod
    def as_view(cls, **initkwargs):
        if 'action' in initkwargs:
            if initkwargs['action'] not in ['serve', 'redirect']:
                raise ImproperlyConfigured("ServeView action must be either 'serve' or 'redirect'")

        return super(ServeView, cls).as_view(**initkwargs)

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

        return getattr(self, self.action)(rendition)

    def serve(self, rendition):
        # Open and serve the file
        rendition.file.open('rb')
        image_format = imghdr.what(rendition.file)
        return StreamingHttpResponse(FileWrapper(rendition.file),
                                     content_type='image/' + image_format)

    def redirect(self, rendition):
        # Redirect to the file's public location
        return HttpResponsePermanentRedirect(rendition.url)


serve = ServeView.as_view()


class SendFileView(ServeView):
    backend = None

    def serve(self, rendition):
        return sendfile(self.request, rendition.file.path, backend=self.backend)
