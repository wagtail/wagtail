from django.http import HttpResponse
from django.core.cache import cache
from django.conf import settings

from .sitemap_generator import Sitemap


def sitemap(request):
    cache_key = 'wagtail-sitemap:' + str(request.site.id)
    sitemap_xml = cache.get(cache_key)

    if not sitemap_xml:
        # Rerender sitemap
        sitemap = Sitemap(request.site)
        sitemap_xml = sitemap.render()

        cache.set(cache_key, sitemap_xml, getattr(settings, 'WAGTAILSITEMAPS_CACHE_TIMEOUT', 6000))

    # Build response
    response = HttpResponse(sitemap_xml)
    response['Content-Type'] = "text/xml; charset=utf-8"

    return response
