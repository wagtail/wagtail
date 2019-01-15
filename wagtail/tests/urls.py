from django.conf.urls import include, url

from wagtail.admin import urls as wagtailadmin_urls
from wagtail.api.v2.endpoints import PagesAPIEndpoint
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.contrib.sitemaps import views as sitemaps_views
from wagtail.contrib.sitemaps import Sitemap
from wagtail.core import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.documents.api.v2.endpoints import DocumentsAPIEndpoint
from wagtail.images import urls as wagtailimages_urls
from wagtail.images.api.v2.endpoints import ImagesAPIEndpoint
from wagtail.images.tests import urls as wagtailimages_test_urls
from wagtail.tests.testapp import urls as testapp_urls
from wagtail.tests.testapp.models import EventSitemap

api_router = WagtailAPIRouter('wagtailapi_v2')
api_router.register_endpoint('pages', PagesAPIEndpoint)
api_router.register_endpoint('images', ImagesAPIEndpoint)
api_router.register_endpoint('documents', DocumentsAPIEndpoint)


urlpatterns = [
    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),
    url(r'^testimages/', include(wagtailimages_test_urls)),
    url(r'^images/', include(wagtailimages_urls)),

    url(r'^api/v2beta/', api_router.urls),
    url(r'^sitemap\.xml$', sitemaps_views.sitemap),

    url(r'^sitemap-index\.xml$', sitemaps_views.index, {
        'sitemaps': {'pages': Sitemap, 'events': EventSitemap(request=None)},
        'sitemap_url_name': 'sitemap',
    }),
    url(r'^sitemap-(?P<section>.+)\.xml$', sitemaps_views.sitemap, name='sitemap'),

    url(r'^testapp/', include(testapp_urls)),

    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's serving mechanism
    url(r'', include(wagtail_urls)),
]
