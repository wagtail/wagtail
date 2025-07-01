from django.db.models import Q
from django.http import Http404
from rest_framework import serializers

from wagtail.api.v2.filters import FieldsFilter, OrderingFilter, SearchFilter
from wagtail.api.v2.serializers import BaseSerializer
from wagtail.api.v2.utils import BadRequestError
from wagtail.api.v2.views import BaseAPIViewSet
from wagtail.contrib.redirects.middleware import get_redirect
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Site


class RedirectSerializer(BaseSerializer):
    location = serializers.CharField(source="link")


class RedirectsAPIViewSet(BaseAPIViewSet):
    base_serializer_class = RedirectSerializer
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    body_fields = BaseAPIViewSet.body_fields + ["old_path", "location"]
    name = "redirects"
    model = Redirect

    known_query_parameters = BaseAPIViewSet.known_query_parameters.union(["site"])

    listing_default_fields = BaseAPIViewSet.listing_default_fields + [
        "old_path",
        "location",
    ]

    def get_queryset(self):
        request = self.request

        queryset = Redirect.objects.all()

        if "site" in request.GET:
            if ":" in request.GET["site"]:
                (hostname, port) = request.GET["site"].split(":", 1)
                query = {
                    "hostname": hostname,
                    "port": port,
                }
            else:
                query = {
                    "hostname": request.GET["site"],
                }
            try:
                site = Site.objects.get(**query)
            except Site.MultipleObjectsReturned:
                raise BadRequestError(
                    "Your query returned multiple sites. Try adding a port number to your site filter."
                )
        else:
            site = Site.find_for_request(self.request)

        if site:
            queryset = queryset.filter(Q(site=site) | Q(site=None))

        return queryset

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
