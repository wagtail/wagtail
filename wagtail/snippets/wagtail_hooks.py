from django.conf.urls import include, url
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.menu import MenuItem
from wagtail.core import hooks
from wagtail.snippets import urls
from wagtail.snippets.models import get_snippet_models
from wagtail.snippets.permissions import user_can_edit_snippets


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^snippets/', include(urls, namespace='wagtailsnippets')),
    ]


class SnippetsMenuItem(MenuItem):
    def is_shown(self, request):
        return user_can_edit_snippets(request.user)


@hooks.register('register_admin_menu_item')
def register_snippets_menu_item():
    return SnippetsMenuItem(
        _('Snippets'),
        reverse('wagtailsnippets:index'),
        classnames='icon icon-snippet',
        order=500
    )


@hooks.register('insert_editor_js')
def editor_js():
    return format_html(
        """
            <script>window.chooserUrls.snippetChooser = '{0}';</script>
        """,
        reverse('wagtailsnippets:choose_generic')
    )


@hooks.register('register_permissions')
def register_permissions():
    content_types = ContentType.objects.get_for_models(*get_snippet_models()).values()
    return Permission.objects.filter(content_type__in=content_types)
