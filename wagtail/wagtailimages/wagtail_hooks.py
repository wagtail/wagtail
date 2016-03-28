from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core import urlresolvers
from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext

from wagtail.wagtailadmin.menu import MenuItem
from wagtail.wagtailadmin.search import SearchArea
from wagtail.wagtailadmin.site_summary import SummaryItem
from wagtail.wagtailcore import hooks
from wagtail.wagtailimages import admin_urls, image_operations
from wagtail.wagtailimages.forms import GroupImagePermissionFormSet
from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtailimages.permissions import permission_policy
from wagtail.wagtailimages.rich_text import ImageEmbedHandler


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^images/', include(admin_urls, namespace='wagtailimages', app_name='wagtailimages')),
    ]


class ImagesMenuItem(MenuItem):
    def is_shown(self, request):
        return permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


@hooks.register('register_admin_menu_item')
def register_images_menu_item():
    return ImagesMenuItem(
        _('Images'), urlresolvers.reverse('wagtailimages:index'),
        name='images', classnames='icon icon-image', order=300
    )


@hooks.register('insert_editor_js')
def editor_js():
    js_files = [
        static('wagtailimages/js/hallo-plugins/hallo-wagtailimage.js'),
        static('wagtailimages/js/image-chooser.js'),
    ]
    js_includes = format_html_join(
        '\n', '<script src="{0}"></script>',
        ((filename, ) for filename in js_files)
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
        return permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


@hooks.register('register_admin_search_area')
def register_images_search_area():
    return ImagesSearchArea(
        _('Images'), urlresolvers.reverse('wagtailimages:index'),
        name='images',
        classnames='icon icon-image',
        order=200)


@hooks.register('register_group_permission_panel')
def register_image_permissions_panel():
    return GroupImagePermissionFormSet


@hooks.register('describe_collection_contents')
def describe_collection_docs(collection):
    images_count = get_image_model().objects.filter(collection=collection).count()
    if images_count:
        url = urlresolvers.reverse('wagtailimages:index') + ('?collection_id=%d' % collection.id)
        return {
            'count': images_count,
            'count_text': ungettext(
                "%(count)s image",
                "%(count)s images",
                images_count
            ) % {'count': images_count},
            'url': url,
        }
