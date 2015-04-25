from django.conf import settings
from django.conf.urls import include, url
from django.core import urlresolvers
from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission

from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem
from wagtail.wagtailadmin.site_summary import SummaryItem

from wagtail.wagtaildocs import admin_urls
from wagtail.wagtaildocs.models import Document
from wagtail.wagtaildocs.rich_text import DocumentLinkHandler


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
    return DocumentsMenuItem(_('Documents'), urlresolvers.reverse('wagtaildocs_index'), name='documents', classnames='icon icon-doc-full-inverse', order=400)


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
    document_permissions = Permission.objects.filter(content_type=document_content_type)
    return document_permissions


@hooks.register('register_rich_text_link_handler')
def register_document_link_handler():
    return ('document', DocumentLinkHandler)


class DocumentsSummaryItem(SummaryItem):
    order = 300
    template = 'wagtaildocs/homepage/site_summary_documents.html'

    def get_context(self):
        return {
            'total_docs': Document.objects.count(),
        }

@hooks.register('construct_homepage_summary_items')
def add_documents_summary_item(request, items):
    items.append(DocumentsSummaryItem(request))
