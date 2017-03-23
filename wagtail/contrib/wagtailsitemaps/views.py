from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.module_loading import import_string

DEFAULT_GENERATOR = 'wagtail.contrib.wagtailsitemaps.sitemap_generator.Sitemap'


def get_generator_class():
    generator_class = getattr(settings, 'WAGTAILSITEMAPS_GENERATOR', DEFAULT_GENERATOR)
    try:
        Sitemap = import_string(generator_class)
    except ImportError:
        Sitemap = import_string(DEFAULT_GENERATOR)

    return Sitemap


def sitemap(request):
    cache_key = 'wagtail-sitemap:' + str(request.site.id)
    sitemap_xml = cache.get(cache_key)

    if not sitemap_xml:
        # Get Sitemap generator class
        Sitemap = get_generator_class()

        # Rerender sitemap
        sitemap = Sitemap(request.site)
        sitemap_xml = sitemap.render()

        cache.set(cache_key, sitemap_xml, getattr(settings, 'WAGTAILSITEMAPS_CACHE_TIMEOUT', 6000))

    # Build response
    response = HttpResponse(sitemap_xml)
    response['Content-Type'] = "text/xml; charset=utf-8"

    return response
