import os
import re

import base64
import hmac
import hashlib

from PIL import Image

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy  as _
from django.conf import settings


def validate_image_format(f):
    # Check file extension
    extension = os.path.splitext(f.name)[1].lower()[1:]

    if extension == 'jpg':
        extension = 'jpeg'

    if extension not in ['gif', 'jpeg', 'png']:
        raise ValidationError(_("Not a valid image. Please use a gif, jpeg or png file with the correct file extension."))

    if not f.closed:
        # Open image file
        file_position = f.tell()
        f.seek(0)
        image = Image.open(f)
        f.seek(file_position)

        # Check that the internal format matches the extension
        if image.format.upper() != extension.upper():
            raise ValidationError(_("Not a valid %s image. Please use a gif, jpeg or png file with the correct file extension.") % (extension.upper()))


def generate_signature(image_id, filter_spec):
    # Based on libthumbor hmac generation
    # https://github.com/thumbor/libthumbor/blob/b19dc58cf84787e08c8e397ab322e86268bb4345/libthumbor/crypto.py#L50
    url = str(image_id) + '/' + str(filter_spec) + '/'
    return base64.urlsafe_b64encode(hmac.new(settings.SECRET_KEY.encode(), url.encode(), hashlib.sha1).digest())


def verify_signature(signature, image_id, filter_spec):
    return signature == generate_signature(image_id, filter_spec)
