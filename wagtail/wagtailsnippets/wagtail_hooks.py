from django.conf import settings
from django.conf.urls import include, url
from django.core import urlresolvers
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem

from wagtail.wagtailsnippets import urls
from wagtail.wagtailsnippets.permissions import user_can_edit_snippets


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^snippets/', include(urls)),
    ]


class SnippetsMenuItem(MenuItem):
    def is_shown(self, request):
        return user_can_edit_snippets(request.user)

@hooks.register('register_admin_menu_item')
def register_snippets_menu_item():
    return SnippetsMenuItem(_('Snippets'), urlresolvers.reverse('wagtailsnippets_index'), classnames='icon icon-snippet', order=500)


@hooks.register('insert_editor_js')
def editor_js():
    return format_html("""
            <script src="{0}{1}"></script>
            <script>window.chooserUrls.snippetChooser = '{2}';</script>
        """,
        settings.STATIC_URL,
        'wagtailsnippets/js/snippet-chooser.js',
        urlresolvers.reverse('wagtailsnippets_choose_generic')
    )
