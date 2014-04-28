from django.conf.urls import include, url

from wagtail.wagtailadmin import hooks
from wagtail.wagtailusers import urls


def register_admin_urls():
    return [
        url(r'^users/', include(urls)),
    ]
hooks.register('register_admin_urls', register_admin_urls)
