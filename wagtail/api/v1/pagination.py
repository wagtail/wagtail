from collections import OrderedDict

from rest_framework.response import Response

from ..shared.pagination import BaseWagtailPagination


class WagtailPagination(BaseWagtailPagination):
    def get_paginated_response(self, data):
        data = OrderedDict([
            ('meta', OrderedDict([
                ('total_count', self.total_count),
            ])),
            (self.view.name, data),
        ])
        return Response(data)
