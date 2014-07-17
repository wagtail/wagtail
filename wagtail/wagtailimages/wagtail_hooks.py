from django.conf import settings
from django.conf.urls import include, url
from django.core import urlresolvers
from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem

from wagtail.wagtailimages import admin_urls


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^images/', include(admin_urls)),
    ]


@hooks.register('construct_main_menu')
def construct_main_menu(request, menu_items):
    if request.user.has_perm('wagtailimages.add_image'):
        menu_items.append(
            MenuItem(_('Images'), urlresolvers.reverse('wagtailimages_index'), classnames='icon icon-image', order=300)
        )


@hooks.register('insert_editor_js')
def editor_js():
    js_files = [
        'wagtailimages/js/hallo-plugins/hallo-wagtailimage.js',
        'wagtailimages/js/image-chooser.js',
    ]
    js_includes = format_html_join('\n', '<script src="{0}{1}"></script>',
        ((settings.STATIC_URL, filename) for filename in js_files)
    )
    return js_includes + format_html(
        """
        <script>
            window.chooserUrls.imageChooser = '{0}';
            registerHalloPlugin('hallowagtailimage');
        </script>
        """,
        urlresolvers.reverse('wagtailimages_chooser')
    )
