import warnings

from django.contrib.sitemaps import Sitemap as DjangoSitemap

from wagtail.core.utils import accepts_kwarg
from wagtail.utils.deprecation import RemovedInWagtail24Warning


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
        site = getattr(self.request, 'site', None)
        if site is None:
            from wagtail.core.models import Site
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

            if not accepts_kwarg(item.get_sitemap_urls, 'request'):
                warnings.warn(
                    "%s.get_sitemap_urls() must be updated to accept an optional "
                    "'request' keyword argument" % type(item).__name__,
                    category=RemovedInWagtail24Warning)

                url_info_items = item.get_sitemap_urls()
            else:
                url_info_items = item.get_sitemap_urls(self.request)

            for url_info in url_info_items:
                urls.append(url_info)
                last_mods.add(url_info.get('lastmod'))

        # last_mods might be empty if the whole site is private
        if last_mods and None not in last_mods:
            self.latest_lastmod = max(last_mods)
        return urls
