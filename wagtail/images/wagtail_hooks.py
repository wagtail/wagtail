from django.urls import include, path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

import wagtail.admin.rich_text.editors.draftail.features as draftail_features

from wagtail.admin.admin_url_finder import ModelAdminURLFinder, register_admin_url_finder
from wagtail.admin.menu import MenuItem
from wagtail.admin.navigation import get_site_for_user
from wagtail.admin.rich_text import HalloPlugin
from wagtail.admin.search import SearchArea
from wagtail.admin.site_summary import SummaryItem
from wagtail.core import hooks
from wagtail.images import admin_urls, get_image_model, image_operations
from wagtail.images.api.admin.views import ImagesAdminAPIViewSet
from wagtail.images.forms import GroupImagePermissionFormSet
from wagtail.images.permissions import permission_policy
from wagtail.images.rich_text import ImageEmbedHandler
from wagtail.images.rich_text.contentstate import ContentstateImageConversionRule
from wagtail.images.rich_text.editor_html import EditorHTMLImageConversionRule
from wagtail.images.views.bulk_actions import (
    AddTagsBulkAction, AddToCollectionBulkAction, DeleteBulkAction)


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        path('images/', include(admin_urls, namespace='wagtailimages')),
    ]


@hooks.register('construct_admin_api')
def construct_admin_api(router):
    router.register_endpoint('images', ImagesAdminAPIViewSet)


class ImagesMenuItem(MenuItem):
    def is_shown(self, request):
        return permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


@hooks.register('register_admin_menu_item')
def register_images_menu_item():
    return ImagesMenuItem(
        _('Images'), reverse('wagtailimages:index'),
        name='images', icon_name='image', order=300
    )


@hooks.register('insert_editor_js')
def editor_js():
    return format_html(
        """
        <script>
            window.chooserUrls.imageChooser = '{0}';
        </script>
        """,
        reverse('wagtailimages:chooser')
    )


@hooks.register('register_rich_text_features')
def register_image_feature(features):
    # define a handler for converting <embed embedtype="image"> tags into frontend HTML
    features.register_embed_type(ImageEmbedHandler)

    # define a hallo.js plugin to use when the 'image' feature is active
    features.register_editor_plugin(
        'hallo', 'image',
        HalloPlugin(
            name='hallowagtailimage',
            js=[
                'wagtailimages/js/image-chooser-modal.js',
                'wagtailimages/js/hallo-plugins/hallo-wagtailimage.js',
            ],
        )
    )

    # define how to convert between editorhtml's representation of images and
    # the database representation
    features.register_converter_rule('editorhtml', 'image', EditorHTMLImageConversionRule)

    # define a draftail plugin to use when the 'image' feature is active
    features.register_editor_plugin(
        'draftail', 'image', draftail_features.EntityFeature({
            'type': 'IMAGE',
            'icon': 'image',
            'description': gettext('Image'),
            # We do not want users to be able to copy-paste hotlinked images into rich text.
            # Keep only the attributes Wagtail needs.
            'attributes': ['id', 'src', 'alt', 'format'],
            # Keep only images which are from Wagtail.
            'whitelist': {
                'id': True,
            }
        }, js=[
            'wagtailimages/js/image-chooser-modal.js',
        ])
    )

    # define how to convert between contentstate's representation of images and
    # the database representation
    features.register_converter_rule('contentstate', 'image', ContentstateImageConversionRule)

    # add 'image' to the set of on-by-default rich text features
    features.default_features.append('image')


@hooks.register('register_image_operations')
def register_image_operations():
    return [
        ('original', image_operations.DoNothingOperation),
        ('fill', image_operations.FillOperation),
        ('min', image_operations.MinMaxOperation),
        ('max', image_operations.MinMaxOperation),
        ('width', image_operations.WidthHeightOperation),
        ('height', image_operations.WidthHeightOperation),
        ('scale', image_operations.ScaleOperation),
        ('jpegquality', image_operations.JPEGQualityOperation),
        ('webpquality', image_operations.WebPQualityOperation),
        ('format', image_operations.FormatOperation),
        ('bgcolor', image_operations.BackgroundColorOperation),
    ]


class ImagesSummaryItem(SummaryItem):
    order = 200
    template_name = 'wagtailimages/homepage/site_summary_images.html'

    def get_context_data(self, parent_context):
        site_name = get_site_for_user(self.request.user)['site_name']

        return {
            'total_images': get_image_model().objects.count(),
            'site_name': site_name,
        }

    def is_shown(self):
        return permission_policy.user_has_any_permission(
            self.request.user, ['add', 'change', 'delete']
        )


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
        _('Images'), reverse('wagtailimages:index'),
        name='images',
        icon_name='image',
        order=200)


@hooks.register('register_group_permission_panel')
def register_image_permissions_panel():
    return GroupImagePermissionFormSet


@hooks.register('describe_collection_contents')
def describe_collection_docs(collection):
    images_count = get_image_model().objects.filter(collection=collection).count()
    if images_count:
        url = reverse('wagtailimages:index') + ('?collection_id=%d' % collection.id)
        return {
            'count': images_count,
            'count_text': ngettext(
                "%(count)s image",
                "%(count)s images",
                images_count
            ) % {'count': images_count},
            'url': url,
        }


class ImageAdminURLFinder(ModelAdminURLFinder):
    edit_url_name = 'wagtailimages:edit'
    permission_policy = permission_policy


register_admin_url_finder(get_image_model(), ImageAdminURLFinder)


for action_class in [AddTagsBulkAction, AddToCollectionBulkAction, DeleteBulkAction]:
    hooks.register('register_bulk_action', action_class)
