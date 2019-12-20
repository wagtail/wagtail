from django.conf.urls import include, url

from wagtail.core import hooks
from wagtail.search.urls import admin as admin_urls


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^search/', include(admin_urls, namespace='wagtailsearch_admin')),
    ]
