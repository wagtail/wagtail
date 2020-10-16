from django.http import HttpResponse
from django.urls import include, path

from wagtail.admin import urls as wagtailadmin_urls
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.contrib.sitemaps import Sitemap
from wagtail.contrib.sitemaps import views as sitemaps_views
from wagtail.core import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.documents.api.v2.views import DocumentsAPIViewSet
from wagtail.images import urls as wagtailimages_urls
from wagtail.images.api.v2.views import ImagesAPIViewSet
from wagtail.images.tests import urls as wagtailimages_test_urls
from wagtail.tests.testapp import urls as testapp_urls
from wagtail.tests.testapp.models import EventSitemap


api_router = WagtailAPIRouter('wagtailapi_v2')
api_router.register_endpoint('pages', PagesAPIViewSet)
api_router.register_endpoint('images', ImagesAPIViewSet)
api_router.register_endpoint('documents', DocumentsAPIViewSet)


urlpatterns = [
    path('admin/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    path('testimages/', include(wagtailimages_test_urls)),
    path('images/', include(wagtailimages_urls)),

    path('api/main/', api_router.urls),
    path('sitemap.xml', sitemaps_views.sitemap),

    path('sitemap-index.xml', sitemaps_views.index, {
        'sitemaps': {'pages': Sitemap, 'events': EventSitemap(request=None)},
        'sitemap_url_name': 'sitemap',
    }),
    path('sitemap-<str:section>.xml', sitemaps_views.sitemap, name='sitemap'),

    path('testapp/', include(testapp_urls)),

    path('fallback/', lambda: HttpResponse('ok'), name='fallback'),

    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's serving mechanism
    path('', include(wagtail_urls)),
]
