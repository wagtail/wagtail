import base64
import hmac
import hashlib

from django.conf import settings


def generate_signature(image_id, filter_spec):
    # Based on libthumbor hmac generation
    # https://github.com/thumbor/libthumbor/blob/b19dc58cf84787e08c8e397ab322e86268bb4345/libthumbor/crypto.py#L50
    url = str(image_id) + '/' + str(filter_spec) + '/'
    return base64.urlsafe_b64encode(hmac.new(settings.SECRET_KEY.encode(), url.encode(), hashlib.sha1).digest())


def verify_signature(signature, image_id, filter_spec):
    return signature == generate_signature(image_id, filter_spec)
