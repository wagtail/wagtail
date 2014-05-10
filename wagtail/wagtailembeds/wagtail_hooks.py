from django.conf import settings
from django.conf.urls import include, url
from django.core import urlresolvers
from django.utils.html import format_html

from wagtail.wagtailadmin import hooks
from wagtail.wagtailembeds import urls


def register_admin_urls():
    return [
        url(r'^embeds/', include(urls)),
    ]
hooks.register('register_admin_urls', register_admin_urls)


def editor_js():
    return format_html("""
            <script src="{0}{1}"></script>
            <script>window.chooserUrls.embedsChooser = '{2}';</script>
        """,
        settings.STATIC_URL,
        'wagtailembeds/js/hallo-plugins/hallo-wagtailembeds.js',
        urlresolvers.reverse('wagtailembeds_chooser')
    )
hooks.register('insert_editor_js', editor_js)
