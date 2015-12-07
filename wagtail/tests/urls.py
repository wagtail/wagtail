from django.conf.urls import include, url

from wagtail.wagtailcore import urls as wagtail_urls
from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls
from wagtail.wagtailimages import urls as wagtailimages_urls
from wagtail.wagtailsearch import urls as wagtailsearch_urls
from wagtail.contrib.wagtailsitemaps.views import sitemap
from wagtail.api.v1 import urls as wagtailapi_urls
from wagtail.api.v2 import urls as wagtailapi2_urls


urlpatterns = [
    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^search/', include(wagtailsearch_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),
    url(r'^images/', include(wagtailimages_urls)),

    url(r'^api/', include(wagtailapi_urls)),
    url(r'^api/', include(wagtailapi2_urls)),
    url(r'^sitemap\.xml$', sitemap),

    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's serving mechanism
    url(r'', include(wagtail_urls)),
]
