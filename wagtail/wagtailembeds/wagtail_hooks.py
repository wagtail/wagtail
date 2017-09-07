from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url
from django.core import urlresolvers
from django.utils.html import format_html

from wagtail.wagtailadmin.rich_text import HalloPlugin
from wagtail.wagtailcore import hooks
from wagtail.wagtailembeds import urls
from wagtail.wagtailembeds.rich_text import MediaEmbedHandler


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^embeds/', include(urls, app_name='wagtailembeds', namespace='wagtailembeds')),
    ]


@hooks.register('insert_editor_js')
def editor_js():
    return format_html(
        """
            <script>
                window.chooserUrls.embedsChooser = '{0}';
                registerHalloPlugin('hallowagtailembeds');
            </script>
        """,
        urlresolvers.reverse('wagtailembeds:chooser')
    )


@hooks.register('register_rich_text_features')
def register_embed_feature(features):
    features.register_editor_plugin(
        'hallo', 'embed',
        HalloPlugin(
            name='hallowagtailembeds',
            js=['wagtailembeds/js/hallo-plugins/hallo-wagtailembeds.js'],
        )
    )
    features.default_features.append('embed')


@hooks.register('register_rich_text_embed_handler')
def register_media_embed_handler():
    return ('media', MediaEmbedHandler)
