from __future__ import absolute_import, unicode_literals

from wagtail.api.v3.endpoints import BaseAPIEndpoint
from wagtail.api.v3.filters import FieldsFilter, OrderingFilter, SearchFilter

from ... import get_image_model
from .serializers import ImageSerializer


class ImagesAPIEndpoint(BaseAPIEndpoint):
    base_serializer_class = ImageSerializer
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    body_fields = BaseAPIEndpoint.body_fields + ['title', 'tags', 'width', 'height']
    meta_fields = BaseAPIEndpoint.meta_fields + []
    listing_default_fields = BaseAPIEndpoint.listing_default_fields + ['title', 'tags']
    nested_default_fields = BaseAPIEndpoint.nested_default_fields + ['title']
    name = 'images'
    model = get_image_model()
