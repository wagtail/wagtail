from django.http import Http404
from rest_framework import serializers

from wagtail.api.v2.filters import FieldsFilter, OrderingFilter, SearchFilter
from wagtail.api.v2.serializers import BaseSerializer
from wagtail.api.v2.views import BaseAPIViewSet
from wagtail.contrib.redirects.middleware import get_redirect
from wagtail.contrib.redirects.models import Redirect


class RedirectSerializer(BaseSerializer):
    location = serializers.CharField(source="link")


class RedirectsAPIViewSet(BaseAPIViewSet):
    base_serializer_class = RedirectSerializer
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    body_fields = BaseAPIViewSet.body_fields + ["old_path", "location"]
    name = "redirects"
    model = Redirect

    listing_default_fields = BaseAPIViewSet.listing_default_fields + [
        "old_path",
        "location",
    ]

    def find_object(self, queryset, request):
        if "html_path" in request.GET:
            redirect = get_redirect(
                request,
                request.GET["html_path"],
            )

            if redirect is None:
                raise Http404
            else:
                return redirect

        return super().find_object(queryset, request)
