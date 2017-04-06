from __future__ import absolute_import, unicode_literals

from ..v2.endpoints import ImagesAPIEndpoint
from .serializers import AdminImageSerializer


class ImagesAdminAPIEndpoint(ImagesAPIEndpoint):
    base_serializer_class = AdminImageSerializer
