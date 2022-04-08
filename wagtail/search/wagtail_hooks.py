from django.urls import include, path

from wagtail import hooks
from wagtail.search.urls import admin as admin_urls


@hooks.register("register_admin_urls")
def register_admin_urls():
    return [
        path("search/", include(admin_urls, namespace="wagtailsearch_admin")),
    ]
