"""An alternative urlconf module where Wagtail front-end URLs
are rooted at '/site/' rather than '/'"""

from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url

from wagtail.admin import urls as wagtailadmin_urls
from wagtail.core import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.images import urls as wagtailimages_urls
from wagtail.search import urls as wagtailsearch_urls

urlpatterns = [
    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^search/', include(wagtailsearch_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),
    url(r'^images/', include(wagtailimages_urls)),
    url(r'^site/', include(wagtail_urls)),
]
