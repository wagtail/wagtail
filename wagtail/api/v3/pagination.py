from math import inf
from typing import Any

from django.conf import settings
from django.db.models import QuerySet
from django.http import HttpRequest
from ninja import Field
from ninja.errors import HttpError
from ninja.pagination import LimitOffsetPagination


def _get_max_limit() -> float | int:
    limit_max = getattr(settings, "WAGTAILAPI_LIMIT_MAX", 20)
    if limit_max is None:
        return inf
    return limit_max


class WagtailLimitOffsetPagination(LimitOffsetPagination):
    """
    Ninja limit/offset pagination with ``WAGTAILAPI_LIMIT_MAX`` enforcement.

    Responses use Ninja's native envelope: ``{"count": N, "items": [...]}``.

    Default ``limit`` is 20 (Wagtail's API default), not Ninja's 100. When
    ``limit`` exceeds ``WAGTAILAPI_LIMIT_MAX`` we raise 400 to match the v2
    API; Ninja's base paginator would silently cap the limit instead.
    """

    class Input(LimitOffsetPagination.Input):
        limit: int = Field(default=20, ge=1)
        offset: int = Field(default=0, ge=0)

    def paginate_queryset(
        self,
        queryset: QuerySet,
        pagination: LimitOffsetPagination.Input,
        request: HttpRequest,
        **params: Any,
    ) -> dict[str, Any]:
        max_limit = _get_max_limit()
        if max_limit != inf and pagination.limit > int(max_limit):
            raise HttpError(400, f"limit cannot be higher than {int(max_limit)}")
        return super().paginate_queryset(queryset, pagination, request, **params)
