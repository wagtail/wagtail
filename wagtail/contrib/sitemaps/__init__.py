import django

from .sitemap_generator import Sitemap  # noqa


if django.VERSION >= (3, 2):
    # The declaration is only needed for older Django versions
    pass
else:
    default_app_config = 'wagtail.contrib.sitemaps.apps.WagtailSitemapsAppConfig'
