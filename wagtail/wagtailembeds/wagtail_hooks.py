from django.conf.urls import include, url
from django.core import urlresolvers
from django.utils.html import format_html
from django.contrib.staticfiles.templatetags.staticfiles import static

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
            <script src="{0}"></script>
            <script>
                window.chooserUrls.embedsChooser = '{1}';
                registerHalloPlugin('hallowagtailembeds');
            </script>
        """,
        static('wagtailembeds/js/hallo-plugins/hallo-wagtailembeds.js'),
        urlresolvers.reverse('wagtailembeds:chooser')
    )


@hooks.register('register_rich_text_embed_handler')
def register_media_embed_handler():
    return ('media', MediaEmbedHandler)
