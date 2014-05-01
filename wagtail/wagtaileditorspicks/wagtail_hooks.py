from django.conf.urls import include, url

from wagtail.wagtailadmin import hooks
from wagtail.wagtaileditorspicks import urls


def register_admin_urls():
    return [
        url(r'^editorspicks/', include(urls)),
    ]
hooks.register('register_admin_urls', register_admin_urls)
