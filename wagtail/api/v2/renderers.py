from django.conf import settings
from django.http import JsonResponse

from wagtail.models import Page, PageViewRestriction, Site
from wagtail.renderers import BasePageRenderer

from .router import WagtailAPIRouter
from .utils import parse_fields_parameter
from .views import PagesAPIViewSet


class APIV2PageRenderer(BasePageRenderer):
    """
    Renders a page using the Wagtail API serializer that can be configured using the `.api_fields` attribute on the page.
    """

    media_type = "application/json; version=2"

    def get_base_queryset(self, request):
        """
        Returns a queryset containing all pages that can be seen by this user.

        This is used as the base for get_queryset and is also used to find the
        parent pages when using the child_of and descendant_of filters as well.
        """
        # Get all live pages
        queryset = Page.objects.all().live()

        # Exclude pages that the user doesn't have access to
        restricted_pages = [
            restriction.page
            for restriction in PageViewRestriction.objects.all().select_related("page")
            if not restriction.accept_request(request)
        ]

        # Exclude the restricted pages and their descendants from the queryset
        for restricted_page in restricted_pages:
            queryset = queryset.not_descendant_of(restricted_page, inclusive=True)

        # Filter by site
        site = Site.find_for_request(request)
        if site:
            base_queryset = queryset
            queryset = base_queryset.descendant_of(site.root_page, inclusive=True)

            # If internationalisation is enabled, include pages from other language trees
            if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
                for translation in site.root_page.get_translations():
                    queryset |= base_queryset.descendant_of(translation, inclusive=True)

        else:
            # No sites configured
            queryset = queryset.none()

        return queryset

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
                "base_queryset": self.get_base_queryset(request),
            },
        )
        return JsonResponse(serializer.data)
