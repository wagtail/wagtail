from wagtail.api.v2.endpoints import BaseAPIEndpoint
from wagtail.api.v2.filters import FieldsFilter, OrderingFilter, SearchFilter

from ... import get_image_model
from .serializers import ImageSerializer


class ImagesAPIEndpoint(BaseAPIEndpoint):
    base_serializer_class = ImageSerializer
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    body_fields = BaseAPIEndpoint.body_fields + ['title', 'width', 'height']
    meta_fields = BaseAPIEndpoint.meta_fields + ['tags', 'download_url']
    listing_default_fields = BaseAPIEndpoint.listing_default_fields + ['title', 'tags', 'download_url']
    nested_default_fields = BaseAPIEndpoint.nested_default_fields + ['title', 'download_url']
    name = 'images'
    model = get_image_model()
