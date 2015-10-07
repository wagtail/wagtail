from django.conf import settings
from django.conf.urls import include, url
from django.core import urlresolvers
from django.utils.html import format_html, format_html_join

from wagtail.wagtailcore import hooks
from wagtail.wagtailembeds import admin_urls
from wagtail.wagtailembeds.rich_text import MediaEmbedHandler


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^embeds/', include(admin_urls, namespace='wagtailembeds')),
    ]


@hooks.register('insert_editor_js')
def editor_js():
    js_files = [
        'wagtailembeds/js/hallo-plugins/hallo-wagtailembeds.js',
        'wagtailembeds/js/embed-chooser.js',
    ]
    js_includes = format_html_join('\n', '<script src="{0}{1}"></script>',
        ((settings.STATIC_URL, filename) for filename in js_files)
    )
    return js_includes + format_html(
        """
        <script>
            window.chooserUrls.embedsChooser = '{0}';
            registerHalloPlugin('hallowagtailembeds');
        </script>
        """,
        urlresolvers.reverse('wagtailembeds:chooser')
    )


@hooks.register('register_rich_text_embed_handler')
def register_media_embed_handler():
    return ('media', MediaEmbedHandler)
