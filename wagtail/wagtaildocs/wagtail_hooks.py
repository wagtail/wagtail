from django.conf import settings
from django.conf.urls import include, url
from django.core import urlresolvers
from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission

from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem

from wagtail.wagtaildocs import admin_urls


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^documents/', include(admin_urls)),
    ]


class DocumentsMenuItem(MenuItem):
    def is_shown(self, request):
        return request.user.has_perm('wagtaildocs.add_document')

@hooks.register('register_admin_menu_item')
def register_documents_menu_item():
    return DocumentsMenuItem(_('Documents'), urlresolvers.reverse('wagtaildocs_index'), classnames='icon icon-doc-full-inverse', order=400)


@hooks.register('insert_editor_js')
def editor_js():
    js_files = [
        'wagtaildocs/js/hallo-plugins/hallo-wagtaildoclink.js',
        'wagtaildocs/js/document-chooser.js',
    ]
    js_includes = format_html_join('\n', '<script src="{0}{1}"></script>',
        ((settings.STATIC_URL, filename) for filename in js_files)
    )
    return js_includes + format_html(
        """
        <script>
            window.chooserUrls.documentChooser = '{0}';
            registerHalloPlugin('hallowagtaildoclink');
        </script>
        """,
        urlresolvers.reverse('wagtaildocs_chooser')
    )


@hooks.register('register_permissions')
def register_permissions():
    document_content_type = ContentType.objects.get(app_label='wagtaildocs', model='document')
    document_permissions = Permission.objects.filter(content_type = document_content_type)
    return document_permissions
