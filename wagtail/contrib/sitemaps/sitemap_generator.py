from django.contrib.sitemaps import Sitemap as DjangoSitemap


# Note: avoid importing models here. This module is imported from __init__.py
# which causes it to be loaded early in startup if wagtail.contrib.sitemaps is
# included in INSTALLED_APPS (not required, but developers are likely to add it
# anyhow) leading to an AppRegistryNotReady exception.


class Sitemap(DjangoSitemap):

    def __init__(self, request=None):
        self.request = request

    def location(self, obj):
        return obj.get_full_url(self.request)

    def lastmod(self, obj):
        # fall back on latest_revision_created_at if last_published_at is null
        # (for backwards compatibility from before last_published_at was added)
        return (obj.last_published_at or obj.latest_revision_created_at)

    def get_wagtail_site(self):
        from wagtail.core.models import Site
        site = Site.find_for_request(self.request)
        if site is None:
            return Site.objects.select_related(
                'root_page'
            ).get(is_default_site=True)
        return site

    def items(self):
        return (
            self.get_wagtail_site()
            .root_page
            .get_descendants(inclusive=True)
            .live()
            .public()
            .order_by('path')
            .specific())

    def _urls(self, page, protocol, domain):
        urls = []
        last_mods = set()

        for item in self.paginator.page(page).object_list:

            url_info_items = item.get_sitemap_urls(self.request)

            for url_info in url_info_items:
                urls.append(url_info)
                last_mods.add(url_info.get('lastmod'))

        # last_mods might be empty if the whole site is private
        if last_mods and None not in last_mods:
            self.latest_lastmod = max(last_mods)
        return urls
