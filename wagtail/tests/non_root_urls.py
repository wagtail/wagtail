"""An alternative urlconf module where Wagtail front-end URLs
are rooted at '/site/' rather than '/'"""

from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url

from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtailcore import urls as wagtail_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls
from wagtail.wagtailimages import urls as wagtailimages_urls
from wagtail.wagtailsearch import urls as wagtailsearch_urls

urlpatterns = [
    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^search/', include(wagtailsearch_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),
    url(r'^images/', include(wagtailimages_urls)),
    url(r'^site/', include(wagtail_urls)),
]
