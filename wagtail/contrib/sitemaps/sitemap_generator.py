from collections import defaultdict
from itertools import islice

from django.contrib.sitemaps import Sitemap as DjangoSitemap

# Note: avoid importing models here. This module is imported from __init__.py
# which causes it to be loaded early in startup if wagtail.contrib.sitemaps is
# included in INSTALLED_APPS (not required, but developers are likely to add it
# anyhow) leading to an AppRegistryNotReady exception.


class Sitemap(DjangoSitemap):
    chunk_size = 2000

    def __init__(self, request=None, alternates=False):
        self.request = request
        self.alternates = alternates

    def location(self, obj):
        return obj.get_full_url(self.request)

    def lastmod(self, obj):
        # fall back on latest_revision_created_at if last_published_at is null
        # (for backwards compatibility from before last_published_at was added)
        return obj.last_published_at or obj.latest_revision_created_at

    def get_wagtail_site(self):
        from wagtail.models import Site

        site = Site.find_for_request(self.request)
        if site is None:
            return Site.objects.select_related("root_page").get(is_default_site=True)
        return site

    def items(self):
        return (
            self.get_wagtail_site()
            .root_page.get_descendants(inclusive=True)
            .live()
            .public()
            .order_by("path")
            .defer_streamfields()
            .specific()
        )

    def get_translations(self, page_instances):
        if not page_instances:
            return  # nothing to do

        model = page_instances[0].get_translation_model()
        translations = (
            model.objects.filter(
                translation_key__in=[page.translation_key for page in page_instances]
            )
            .select_related("locale")
            .live()
            .public()
            .defer_streamfields()
            .specific()
        )
        return translations

    def prefetch_translated_objects(self, page_instances):
        """
        Populate translated page caches for a list of page instances
        """
        trans_obj_cache = defaultdict(list)
        for trans_obj in self.get_translations(page_instances):
            trans_obj_cache[trans_obj.translation_key].append(trans_obj)
        for page in page_instances:
            page._translations_cache = trans_obj_cache[page.translation_key]

    def translated_iterator(self, iterator):
        while results := list(islice(iterator, self.chunk_size)):
            self.prefetch_translated_objects(results)
            yield from results

    def _urls(self, page, protocol, domain):
        urls = []
        last_mods = set()

        iterator = self.paginator.page(page).object_list.iterator(self.chunk_size)
        if self.alternates:
            iterator = self.translated_iterator(iterator)
        for item in iterator:
            url_info_items = item.get_sitemap_urls(self.request)

            for url_info in url_info_items:
                urls.append(url_info)
                last_mods.add(url_info.get("lastmod"))

        # last_mods might be empty if the whole site is private
        if last_mods and None not in last_mods:
            self.latest_lastmod = max(last_mods)
        return urls
