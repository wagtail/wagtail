from __future__ import absolute_import, unicode_literals

from rest_framework.filters import BaseFilterBackend

from wagtail.api.v2.utils import BadRequestError


class HasChildrenFilter(BaseFilterBackend):
    """
    Filters the queryset by checking if the pages have children or not.
    This is useful when you want to get just the branches or just the leaves.
    """
    def filter_queryset(self, request, queryset, view):
        if 'has_children' in request.GET:
            try:
                has_children_filter = int(request.GET['has_children'])
                assert has_children_filter is 1 or has_children_filter is 0
            except (ValueError, AssertionError):
                raise BadRequestError("has_children must be 1 or 0")

            if has_children_filter == 1:
                return queryset.filter(numchild__gt=0)
            else:
                return queryset.filter(numchild=0)

        return queryset
