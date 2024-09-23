from ..v2.views import ImagesAPIViewSet
from .serializers import AdminImageSerializer


class ImagesAdminAPIViewSet(ImagesAPIViewSet):
    base_serializer_class = AdminImageSerializer

    body_fields = ImagesAPIViewSet.body_fields + [
        "thumbnail",
    ]

    listing_default_fields = ImagesAPIViewSet.listing_default_fields + [
        "width",
        "height",
        "thumbnail",
    ]
