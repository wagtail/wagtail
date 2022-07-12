from django.http import Http404
from django.urls import path
from rest_framework import serializers, viewsets

from wagtail.contrib.redirects.middleware import get_redirect
from wagtail.contrib.redirects.models import Redirect


class RedirectSerializer(serializers.ModelSerializer):
    location = serializers.CharField(source="link")

    class Meta:
        model = Redirect
        fields = ("is_permanent", "location")


class RedirectsAPIViewSet(viewsets.ReadOnlyModelViewSet):
    model = Redirect
    serializer_class = RedirectSerializer

    def get_object(self):
        request = self.request

        if "html_path" in request.GET:
            redirect = get_redirect(
                request, request.GET["html_path"], exact_match=False
            )
            if redirect is not None:
                return redirect

        raise Http404()

    @classmethod
    def get_urlpatterns(cls):
        """
        This returns a list of URL patterns for the endpoint
        """
        return [
            path("find/", cls.as_view({"get": "retrieve"}), name="detail"),
        ]
