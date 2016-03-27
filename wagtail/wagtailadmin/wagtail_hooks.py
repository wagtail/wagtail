from django import forms
from django.core import urlresolvers
from django.contrib.auth.models import Permission
from django.utils.translation import ugettext_lazy as _
from django.contrib.staticfiles.templatetags.staticfiles import static

from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.permissions import collection_permission_policy
from wagtail.wagtailadmin.menu import MenuItem, SubmenuMenuItem, settings_menu
from wagtail.wagtailadmin.search import SearchArea


class ExplorerMenuItem(MenuItem):
    @property
    def media(self):
        return forms.Media(js=[static('wagtailadmin/js/explorer-menu.js')])


@hooks.register('register_admin_menu_item')
def register_explorer_menu_item():
    return ExplorerMenuItem(
        _('Explorer'), urlresolvers.reverse('wagtailadmin_explore_root'),
        name='explorer',
        classnames='icon icon-folder-open-inverse dl-trigger',
        attrs={'data-explorer-menu-url': urlresolvers.reverse('wagtailadmin_explorer_nav')},
        order=100)


@hooks.register('register_admin_menu_item')
def register_settings_menu():
    return SubmenuMenuItem(
        _('Settings'), settings_menu, classnames='icon icon-cogs', order=10000)


@hooks.register('register_permissions')
def register_permissions():
    return Permission.objects.filter(content_type__app_label='wagtailadmin', codename='access_admin')


@hooks.register('register_admin_search_area')
def register_pages_search_area():
    return SearchArea(
        _('Pages'), urlresolvers.reverse('wagtailadmin_pages:search'),
        name='pages',
        classnames='icon icon-folder-open-inverse',
        order=100)


class CollectionsMenuItem(MenuItem):
    def is_shown(self, request):
        return collection_permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


@hooks.register('register_settings_menu_item')
def register_collections_menu_item():
    return CollectionsMenuItem(_('Collections'), urlresolvers.reverse('wagtailadmin_collections:index'), classnames='icon icon-folder-open-1', order=700)
