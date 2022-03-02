from wagtail.api.v2.filters import FieldsFilter, OrderingFilter, SearchFilter
from wagtail.api.v2.views import BaseAPIViewSet

from ... import get_image_model
from .serializers import ImageSerializer


class ImagesAPIViewSet(BaseAPIViewSet):
    base_serializer_class = ImageSerializer
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    body_fields = BaseAPIViewSet.body_fields + ["title", "width", "height"]
    meta_fields = BaseAPIViewSet.meta_fields + ["tags", "download_url"]
    listing_default_fields = BaseAPIViewSet.listing_default_fields + [
        "title",
        "tags",
        "download_url",
    ]
    nested_default_fields = BaseAPIViewSet.nested_default_fields + [
        "title",
        "download_url",
    ]
    name = "images"
    model = get_image_model()
