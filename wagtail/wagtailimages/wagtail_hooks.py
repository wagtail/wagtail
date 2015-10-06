from django.conf import settings
from django.conf.urls import include, url
from django.core import urlresolvers
from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Permission

from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem
from wagtail.wagtailadmin.site_summary import SummaryItem
from wagtail.wagtailadmin.search import SearchArea

from wagtail.wagtailimages import admin_urls, image_operations
from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtailimages.rich_text import ImageEmbedHandler


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^images/', include(admin_urls, namespace='wagtailimages', app_name='wagtailimages')),
    ]


class ImagesMenuItem(MenuItem):
    def is_shown(self, request):
        return request.user.has_perm('wagtailimages.add_image') or request.user.has_perm('wagtailimages.change_image')


@hooks.register('register_admin_menu_item')
def register_images_menu_item():
    return ImagesMenuItem(
        _('Images'), urlresolvers.reverse('wagtailimages:index'),
        name='images', classnames='icon icon-image', order=300
    )


@hooks.register('insert_editor_js')
def editor_js():
    js_files = [
        'wagtailimages/js/hallo-plugins/hallo-wagtailimage.js',
        'wagtailimages/js/image-chooser.js',
    ]
    js_includes = format_html_join(
        '\n', '<script src="{0}{1}"></script>',
        ((settings.STATIC_URL, filename) for filename in js_files)
    )
    return js_includes + format_html(
        """
        <script>
            window.chooserUrls.imageChooser = '{0}';
            registerHalloPlugin('hallowagtailimage');
        </script>
        """,
        urlresolvers.reverse('wagtailimages:chooser')
    )


@hooks.register('register_permissions')
def register_permissions():
    return Permission.objects.filter(content_type__app_label='wagtailimages',
                                     codename__in=['add_image', 'change_image'])


@hooks.register('register_image_operations')
def register_image_operations():
    return [
        ('original', image_operations.DoNothingOperation),
        ('fill', image_operations.FillOperation),
        ('min', image_operations.MinMaxOperation),
        ('max', image_operations.MinMaxOperation),
        ('width', image_operations.WidthHeightOperation),
        ('height', image_operations.WidthHeightOperation),
    ]


@hooks.register('register_rich_text_embed_handler')
def register_image_embed_handler():
    return ('image', ImageEmbedHandler)


class ImagesSummaryItem(SummaryItem):
    order = 200
    template = 'wagtailimages/homepage/site_summary_images.html'

    def get_context(self):
        return {
            'total_images': get_image_model().objects.count(),
        }


@hooks.register('construct_homepage_summary_items')
def add_images_summary_item(request, items):
    items.append(ImagesSummaryItem(request))


class ImagesSearchArea(SearchArea):
    def is_shown(self, request):
        return request.user.has_perm('wagtailimages.add_image') or request.user.has_perm('wagtailimages.change_image')


@hooks.register('register_admin_search_area')
def register_images_search_area():
    return ImagesSearchArea(
        _('Images'), urlresolvers.reverse('wagtailimages:index'),
        name='images',
        classnames='icon icon-image',
        order=200)
