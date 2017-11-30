from django.conf.urls import include, url

from wagtail.core import hooks

from . import urls


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^settings/', include(urls, namespace='wagtailsettings')),
    ]
