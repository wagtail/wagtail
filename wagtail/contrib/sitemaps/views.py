import inspect

from django.contrib.sitemaps import views as sitemap_views

from .sitemap_generator import Sitemap


def index(request, sitemaps, **kwargs):
    sitemaps = prepare_sitemaps(request, sitemaps)
    return sitemap_views.index(request, sitemaps, **kwargs)


def sitemap(request, sitemaps=None, **kwargs):
    if sitemaps:
        sitemaps = prepare_sitemaps(request, sitemaps)
    else:
        sitemaps = {'wagtail': Sitemap(request)}
    return sitemap_views.sitemap(request, sitemaps, **kwargs)


def prepare_sitemaps(request, sitemaps):
    initialised_sitemaps = {}
    for name, sitemap_cls in sitemaps.items():
        if inspect.isclass(sitemap_cls) and issubclass(sitemap_cls, Sitemap):
            initialised_sitemaps[name] = sitemap_cls(request)
        else:
            initialised_sitemaps[name] = sitemap_cls
    return initialised_sitemaps
