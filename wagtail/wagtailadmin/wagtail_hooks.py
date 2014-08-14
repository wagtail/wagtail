from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem, SubmenuMenuItem, settings_menu


class ExplorerMenuItem(MenuItem):
    class Media:
        js = ['wagtailadmin/js/explorer-menu.js']

@hooks.register('register_admin_menu_item')
def register_explorer_menu_item():
    return ExplorerMenuItem(
        _('Explorer'), urlresolvers.reverse('wagtailadmin_explore_root'),
        classnames='icon icon-folder-open-inverse dl-trigger',
        attrs={'data-explorer-menu-url': urlresolvers.reverse('wagtailadmin_explorer_nav')},
        order=100)

@hooks.register('register_admin_menu_item')
def register_search_menu_item():
    return MenuItem(
        _('Search'), urlresolvers.reverse('wagtailadmin_pages_search'),
        classnames='icon icon-search', order=200)


@hooks.register('register_admin_menu_item')
def register_settings_menu():
    return SubmenuMenuItem(
        _('Settings'), settings_menu, classnames='icon icon-cogs', order=10000)
