from django.contrib.sitemaps import Sitemap as DjangoSitemap
from django.db.models.functions import Coalesce
from django.utils.functional import cached_property

# Note: avoid importing models here. This module is imported from __init__.py
# which causes it to be loaded early in startup if wagtail.contrib.sitemaps is
# included in INSTALLED_APPS (not required, but developers are likely to add it
# anyhow) leading to an AppRegistryNotReady exception.


class Sitemap(DjangoSitemap):
    def __init__(self, request=None):
        self.request = request

    def location(self, obj):
        return obj.get_full_url(self.request)

    def get_latest_lastmod(self):
        return (
            self.items()
            .annotate(
                lastmod=Coalesce("last_published_at", "latest_revision_created_at")
            )
            .order_by("-lastmod")
            .values_list("lastmod", flat=True)
            .first()
        )

    @cached_property
    def wagtail_site(self):
        from wagtail.models import Site

        site = Site.find_for_request(self.request)
        if site is None:
            return Site.objects.select_related("root_page").get(is_default_site=True)
        return site

    def items(self):
        return (
            self.wagtail_site.root_page.get_descendants(inclusive=True)
            .live()
            .public()
            .order_by("path")
            .specific(defer=True)
        )

    def _urls(self, page, protocol, domain):
        urls = []
        latest_lastmod = None
        all_items_lastmod = True  # track if all items have a lastmod

        for item in self.paginator.page(page).object_list.iterator():
            for url_info in item.get_sitemap_urls(self.request):
                urls.append(url_info)
                if all_items_lastmod:
                    lastmod = url_info.get("lastmod")
                    all_items_lastmod = lastmod is not None
                    if all_items_lastmod and (
                        latest_lastmod is None or lastmod > latest_lastmod
                    ):
                        latest_lastmod = lastmod

        if all_items_lastmod and latest_lastmod:
            self.latest_lastmod = latest_lastmod

        return urls
