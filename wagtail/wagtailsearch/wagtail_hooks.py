from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url

from wagtail.wagtailcore import hooks
from wagtail.wagtailsearch.urls import admin as admin_urls


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^search/', include(admin_urls, namespace='wagtailsearch_admin')),
    ]
