from __future__ import absolute_import, unicode_literals

from ..v2.endpoints import ImagesAPIEndpoint
from .serializers import AdminImageSerializer


class ImagesAdminAPIEndpoint(ImagesAPIEndpoint):
    base_serializer_class = AdminImageSerializer

    extra_body_fields = ImagesAPIEndpoint.extra_body_fields + [
        'thumbnail',
    ]

    default_fields = ImagesAPIEndpoint.default_fields + [
        'width',
        'height',
        'thumbnail',
    ]
