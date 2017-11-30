from django.contrib.sitemaps import Sitemap as DjangoSitemap


class Sitemap(DjangoSitemap):

    def __init__(self, site=None):
        self.site = site

    def location(self, obj):
        return obj.url

    def lastmod(self, obj):
        # fall back on latest_revision_created_at if last_published_at is null
        # (for backwards compatibility from before last_published_at was added)
        return (obj.last_published_at or obj.latest_revision_created_at)

    def items(self):
        return (
            self.site
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
            for url_info in item.get_sitemap_urls():
                urls.append(url_info)
                last_mods.add(url_info.get('lastmod'))

        # last_mods might be empty if the whole site is private
        if last_mods and None not in last_mods:
            self.latest_lastmod = max(last_mods)
        return urls
