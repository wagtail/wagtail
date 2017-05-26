from __future__ import absolute_import, unicode_literals

from django.contrib.sitemaps import Sitemap as DjangoSitemap


class Sitemap(DjangoSitemap):

    def __init__(self, site=None):
        self.site = site

    def location(self, obj):
        return obj.specific.url

    def lastmod(self, obj):
        return obj.specific.latest_revision_created_at

    def items(self):
        return (
            self.site
            .root_page
            .get_descendants(inclusive=True)
            .live()
            .public()
            .order_by('path'))

    def _urls(self, page, protocol, domain):
        urls = []
        last_mods = set()

        for item in self.paginator.page(page).object_list:
            for url_info in item.specific.get_sitemap_urls():
                urls.append(url_info)
                last_mods.add(url_info.get('lastmod'))

        if None not in last_mods:
            self.latest_lastmod = max(last_mods)
        return urls
