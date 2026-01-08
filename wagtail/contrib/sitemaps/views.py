import inspect

from django.conf import settings
from django.contrib.sitemaps import views as sitemap_views

from .sitemap_generator import Sitemap


def index(request, sitemaps, **kwargs):
    sitemaps = prepare_sitemaps(request, sitemaps)
    return sitemap_views.index(request, sitemaps, **kwargs)


def sitemap(request, sitemaps=None, alternates=None, **kwargs):
    if alternates is None:
        alternates = getattr(settings, "WAGTAIL_I18N_ENABLED", False)
    if sitemaps:
        sitemaps = prepare_sitemaps(request, sitemaps, alternates=alternates)
    else:
        sitemaps = {"wagtail": Sitemap(request, alternates=alternates)}
    return sitemap_views.sitemap(request, sitemaps, **kwargs)


def prepare_sitemaps(request, sitemaps, alternates=False):
    initialised_sitemaps = {}
    for name, sitemap_cls in sitemaps.items():
        if inspect.isclass(sitemap_cls) and issubclass(sitemap_cls, Sitemap):
            initialised_sitemaps[name] = sitemap_cls(request, alternates=alternates)
        else:
            initialised_sitemaps[name] = sitemap_cls
    return initialised_sitemaps
