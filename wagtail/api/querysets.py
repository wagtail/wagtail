import swapper
from django.conf import settings

from wagtail.api.validators import SiteFilterValidator
from wagtail.models import PageViewRestriction

Page = swapper.load_model("wagtailcore", "Page")


def get_public_pages_queryset(request, model=Page):
    """
    Returns a queryset containing all live, public pages visible to anonymous
    API consumers, scoped to the requested site.

    Shared by the v2 pages API and the v3 public read tier.
    """
    queryset = model._default_manager.all().live()

    # Exclude pages that the user doesn't have access to
    restricted_pages = [
        restriction.page
        for restriction in PageViewRestriction.objects.all().select_related("page")
        if not restriction.accept_request(request)
    ]

    # Exclude the restricted pages and their descendants from the queryset
    for restricted_page in restricted_pages:
        queryset = queryset.not_descendant_of(restricted_page, inclusive=True)

    # Check if we have a specific site to look for
    site = SiteFilterValidator(site=request.GET.get("site"), request=request).site_obj

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
