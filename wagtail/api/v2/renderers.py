from django.http import JsonResponse

from wagtail.renderers import BasePageRenderer

from .router import WagtailAPIRouter
from .utils import get_base_queryset, parse_fields_parameter
from .views import PagesAPIViewSet


class APIV2PageRenderer(BasePageRenderer):
    """
    Renders a page using the Wagtail API serializer that can be configured using the `.api_fields` attribute on the page.
    """

    media_type = "application/json; version=2"

    def get_serializer_class(self, request, page, router):
        return PagesAPIViewSet._get_serializer_class(
            router,
            type(page),
            parse_fields_parameter("-detail_url"),
            show_details=True,
        )

    def render(self, request, media_type, page, args, kwargs):
        router = WagtailAPIRouter("")
        serializer_class = self.get_serializer_class(request, page, router)
        serializer = serializer_class(
            page,
            context={
                "request": request,
                "router": router,
                "base_queryset": get_base_queryset(request),
            },
        )
        return JsonResponse(serializer.data)
