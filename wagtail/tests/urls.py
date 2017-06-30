from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url

from wagtail.api.v2.endpoints import PagesAPIEndpoint as PagesAPIEndpointV2
from wagtail.api.v2.router import WagtailAPIRouter as WagtailAPIRouterV2
from wagtail.api.v3.endpoints import PagesAPIEndpoint as PagesAPIEndpointV3
from wagtail.api.v3.router import WagtailAPIRouter as WagtailAPIRouterV3
from wagtail.contrib.wagtailapi import urls as wagtailapi_urls
from wagtail.contrib.wagtailsitemaps import views as sitemaps_views
from wagtail.contrib.wagtailsitemaps import Sitemap
from wagtail.tests.testapp import urls as testapp_urls
from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtailcore import urls as wagtail_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls
from wagtail.wagtaildocs.api.v2.endpoints import DocumentsAPIEndpoint as DocumentsAPIEndpointV2
from wagtail.wagtaildocs.api.v3.endpoints import DocumentsAPIEndpoint as DocumentsAPIEndpointV3
from wagtail.wagtailimages import urls as wagtailimages_urls
from wagtail.wagtailimages.api.v2.endpoints import ImagesAPIEndpoint as ImagesAPIEndpointV2
from wagtail.wagtailimages.api.v3.endpoints import ImagesAPIEndpoint as ImagesAPIEndpointV3
from wagtail.wagtailimages.tests import urls as wagtailimages_test_urls
from wagtail.wagtailsearch import urls as wagtailsearch_urls


api_router_v2 = WagtailAPIRouterV2('wagtailapi_v2')
api_router_v2.register_endpoint('pages', PagesAPIEndpointV2)
api_router_v2.register_endpoint('images', ImagesAPIEndpointV2)
api_router_v2.register_endpoint('documents', DocumentsAPIEndpointV2)


api_router_v3 = WagtailAPIRouterV3('wagtailapi_v3')
api_router_v3.register_endpoint('pages', PagesAPIEndpointV3)
api_router_v3.register_endpoint('images', ImagesAPIEndpointV3)
api_router_v3.register_endpoint('documents', DocumentsAPIEndpointV3)


urlpatterns = [
    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^search/', include(wagtailsearch_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),
    url(r'^testimages/', include(wagtailimages_test_urls)),
    url(r'^images/', include(wagtailimages_urls)),

    url(r'^api/', include(wagtailapi_urls)),
    url(r'^api/v2beta/', api_router_v2.urls),
    url(r'^api/v3beta/', api_router_v3.urls),
    url(r'^sitemap\.xml$', sitemaps_views.sitemap),

    url(r'^sitemap-index\.xml$', sitemaps_views.index, {
        'sitemaps': {'pages': Sitemap},
        'sitemap_url_name': 'sitemap',
    }),
    url(r'^sitemap-(?P<section>.+)\.xml$', sitemaps_views.sitemap, name='sitemap'),

    url(r'^testapp/', include(testapp_urls)),

    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's serving mechanism
    url(r'', include(wagtail_urls)),
]
