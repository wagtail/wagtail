from django.conf.urls import include, url
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext, ungettext

import wagtail.admin.rich_text.editors.draftail.features as draftail_features
from wagtail.admin.menu import MenuItem
from wagtail.admin.rich_text import HalloPlugin
from wagtail.admin.search import SearchArea
from wagtail.admin.site_summary import SummaryItem
from wagtail.core import hooks
from wagtail.images import admin_urls, get_image_model, image_operations
from wagtail.images.api.admin.endpoints import ImagesAdminAPIEndpoint
from wagtail.images.forms import GroupImagePermissionFormSet
from wagtail.images.permissions import permission_policy
from wagtail.images.rich_text import (
    ContentstateImageConversionRule, EditorHTMLImageConversionRule, image_embedtype_handler)


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^images/', include(admin_urls, namespace='wagtailimages')),
    ]


@hooks.register('construct_admin_api')
def construct_admin_api(router):
    router.register_endpoint('images', ImagesAdminAPIEndpoint)


class ImagesMenuItem(MenuItem):
    def is_shown(self, request):
        return permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


@hooks.register('register_admin_menu_item')
def register_images_menu_item():
    return ImagesMenuItem(
        _('Images'), reverse('wagtailimages:index'),
        name='images', classnames='icon icon-image', order=300
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
    features.register_embed_type('image', image_embedtype_handler)

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
            'description': ugettext('Image'),
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
        ('jpegquality', image_operations.JPEGQualityOperation),
        ('format', image_operations.FormatOperation),
        ('bgcolor', image_operations.BackgroundColorOperation),
    ]


class ImagesSummaryItem(SummaryItem):
    order = 200
    template = 'wagtailimages/homepage/site_summary_images.html'

    def get_context(self):
        return {
            'total_images': get_image_model().objects.count(),
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
        classnames='icon icon-image',
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
            'count_text': ungettext(
                "%(count)s image",
                "%(count)s images",
                images_count
            ) % {'count': images_count},
            'url': url,
        }
