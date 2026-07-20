from django.conf import settings

from wagtail.api.v2.utils import BadRequestError
from wagtail.models import Page, PageViewRestriction, Site


def get_public_pages_queryset(request):
    """
    Returns a queryset containing all live, public pages visible to anonymous
    API consumers, scoped to the requested site.

    Shared by the v2 pages API and the v3 public read tier.
    """
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

    # Check if we have a specific site to look for
    if "site" in request.GET:
        # Optionally allow querying by port
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
        except Site.MultipleObjectsReturned as e:
            raise BadRequestError(
                "Your query returned multiple sites. Try adding a port number to your site filter."
            ) from e
    else:
        # Otherwise, find the site from the request
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
