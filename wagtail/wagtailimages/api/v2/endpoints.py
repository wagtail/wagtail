from __future__ import absolute_import, unicode_literals

from wagtail.api.v2.endpoints import BaseAPIEndpoint
from wagtail.api.v2.filters import FieldsFilter, OrderingFilter, SearchFilter

from ...models import get_image_model
from .serializers import ImageSerializer



class ImagesAPIEndpoint(BaseAPIEndpoint):
    base_serializer_class = ImageSerializer
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    body_fields = BaseAPIEndpoint.body_fields + ['title', 'width', 'height']
    meta_fields = BaseAPIEndpoint.meta_fields + ['tags']
    default_fields = BaseAPIEndpoint.default_fields + ['title', 'tags']
    name = 'images'
    model = get_image_model()
