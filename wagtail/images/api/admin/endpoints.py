from ..v2.endpoints import ImagesAPIEndpoint
from .serializers import AdminImageSerializer


class ImagesAdminAPIEndpoint(ImagesAPIEndpoint):
    base_serializer_class = AdminImageSerializer

    body_fields = ImagesAPIEndpoint.body_fields + [
        'thumbnail',
    ]

    listing_default_fields = ImagesAPIEndpoint.listing_default_fields + [
        'width',
        'height',
        'thumbnail',
    ]
