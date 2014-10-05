from django.conf import settings
from django.conf.urls import include, url
from django.core import urlresolvers
from django.core.exceptions import ImproperlyConfigured
from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem

from wagtail.wagtailimages import admin_urls


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^images/', include(admin_urls)),
    ]


# Check for the presence of a pre-Wagtail-0.3-style urlconf, and fail loudly if one is found.
# Prior to Wagtail 0.3, the standard Wagtail urls.py contained an entry for
# wagtail.wagtailimages.urls rooted at '/admin/images/' or equivalent. As of Wagtail 0.5,
# the wagtailimages admin views are defined by wagtail.wagtailimages.admin_urls, and
# wagtail.wagtailimages.urls is used for front-end views instead - which means that those URLs
# will clash with the admin.
# This check can only be performed after the ROOT_URLCONF module has been fully imported. Since
# importing a urlconf module generally involves recursively importing a whole load of other things
# including models.py and wagtail_hooks.py, there is no obvious place to put this code at the
# module level without causing a circular import. We therefore put it in construct_main_menu, which
# is run frequently enough to ensure that the error message will not be missed. Yes, it's hacky :-(

OLD_STYLE_URLCONF_CHECK_PASSED = False
def check_old_style_urlconf():
    global OLD_STYLE_URLCONF_CHECK_PASSED

    # A faulty urls.py will place wagtail.wagtailimages.urls at the same path that
    # wagtail.wagtailimages.admin_urls is loaded to, resulting in the wagtailimages_serve path
    # being equal to wagtailimages_index followed by three arbitrary args
    try:
        wagtailimages_serve_path = urlresolvers.reverse('wagtailimages_serve', args = ['123', '456', '789'])
    except urlresolvers.NoReverseMatch:
        # wagtailimages_serve is not defined at all, so there's no collision
        OLD_STYLE_URLCONF_CHECK_PASSED = True
        return

    wagtailimages_index_path = urlresolvers.reverse('wagtailimages_index')
    if wagtailimages_serve_path == wagtailimages_index_path + '123/456/789/':
        raise ImproperlyConfigured("""Your urls.py contains an entry for %s that needs to be removed.
            See http://wagtail.readthedocs.org/en/latest/releases/0.5.html#urlconf-entries-for-admin-images-admin-embeds-etc-need-to-be-removed"""
            % wagtailimages_index_path
        )
    else:
        OLD_STYLE_URLCONF_CHECK_PASSED = True


@hooks.register('construct_main_menu')
def construct_main_menu(request, menu_items):
    if not OLD_STYLE_URLCONF_CHECK_PASSED:
        check_old_style_urlconf()


class ImagesMenuItem(MenuItem):
    def is_shown(self, request):
        return request.user.has_perm('wagtailimages.add_image')

@hooks.register('register_admin_menu_item')
def register_images_menu_item():
    return ImagesMenuItem(_('Images'), urlresolvers.reverse('wagtailimages_index'), classnames='icon icon-image', order=300)


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


@hooks.register('register_permissions')
def register_permissions():
    image_content_type = ContentType.objects.get(app_label='wagtailimages', model='image')
    image_permissions = Permission.objects.filter(content_type = image_content_type)
    return image_permissions
