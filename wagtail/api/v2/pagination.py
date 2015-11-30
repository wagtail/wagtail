from collections import OrderedDict

from rest_framework.response import Response

from ..shared.pagination import BaseWagtailPagination


class WagtailPagination(BaseWagtailPagination):
    def get_paginated_response(self, data):
        data = OrderedDict([
            ('total_count', self.total_count),
            ('results', data),
        ])
        return Response(data)
