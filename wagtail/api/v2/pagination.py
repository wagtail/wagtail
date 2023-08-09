from collections import OrderedDict

from django.conf import settings
from rest_framework.pagination import BasePagination
from rest_framework.response import Response

from .utils import BadRequestError


class WagtailPagination(BasePagination):
    def paginate_queryset(self, queryset, request, view=None):
        limit_max = getattr(settings, "WAGTAILAPI_LIMIT_MAX", 20)

        try:
            offset = int(request.GET.get("offset", 0))
            if offset < 0:
                raise ValueError()
        except ValueError:
            raise BadRequestError("offset must be a positive integer")

        try:
            limit_default = 20 if not limit_max else min(20, limit_max)
            limit = int(request.GET.get("limit", limit_default))
            if limit < 0:
                raise ValueError()
        except ValueError:
            raise BadRequestError("limit must be a positive integer")

        if limit_max and limit > limit_max:
            raise BadRequestError("limit cannot be higher than %d" % limit_max)

        start = offset
        stop = offset + limit

        self.view = view
        self.total_count = queryset.count()
        return queryset[start:stop]

    def get_paginated_response(self, data):
        data = OrderedDict(
            [
                (
                    "meta",
                    OrderedDict(
                        [
                            ("total_count", self.total_count),
                        ]
                    ),
                ),
                ("items", data),
            ]
        )
        return Response(data)
