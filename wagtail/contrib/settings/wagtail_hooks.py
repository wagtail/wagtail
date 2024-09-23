from django.urls import include, path

from wagtail import hooks

from . import urls


@hooks.register("register_admin_urls")
def register_admin_urls():
    return [
        path("settings/", include(urls, namespace="wagtailsettings")),
    ]
