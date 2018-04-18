from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns

from wagtail.core import urls as wagtail_urls


urlpatterns = i18n_patterns(url(r'', include(wagtail_urls)))
