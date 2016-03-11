from django.contrib.auth.models import Permission
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.menu import MenuItem, SubmenuMenuItem, settings_menu
from wagtail.wagtailadmin.search import SearchArea
from wagtail.wagtailadmin.widgets import Button, ButtonWithDropdownFromHook, PageListingButton
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.permissions import collection_permission_policy


class ExplorerMenuItem(MenuItem):
    class Media:
        js = [static('wagtailadmin/js/explorer-menu.js')]


@hooks.register('register_admin_menu_item')
def register_explorer_menu_item():
    return ExplorerMenuItem(
        _('Explorer'), reverse('wagtailadmin_explore_root'),
        name='explorer',
        classnames='icon icon-folder-open-inverse dl-trigger',
        attrs={'data-explorer-menu-url': reverse('wagtailadmin_explorer_nav')},
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
        _('Pages'), reverse('wagtailadmin_pages:search'),
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
    return CollectionsMenuItem(_('Collections'), reverse('wagtailadmin_collections:index'), classnames='icon icon-folder-open-1', order=700)


@hooks.register('register_page_listing_buttons')
def page_listing_buttons(page, page_perms, is_parent=False):
    if page_perms.can_edit():
        yield PageListingButton(_('Edit'), reverse('wagtailadmin_pages:edit', args=[page.id]),
                                attrs={'title': _('Edit this page')}, priority=10)
    if page.has_unpublished_changes:
        yield PageListingButton(_('Draft'), reverse('wagtailadmin_pages:view_draft', args=[page.id]),
                                attrs={'target': '_blank'}, priority=20)
    if page.live and page.url:
        yield PageListingButton(_('Live'), page.url, attrs={'target': "_blank"}, priority=30)
    if page_perms.can_add_subpage():
        if is_parent:
            yield Button(_('Add child page'), reverse('wagtailadmin_pages:add_subpage', args=[page.id]),
                         classes={'button', 'button-small', 'bicolor', 'icon', 'white', 'icon-plus'}, priority=40)
        else:
            yield PageListingButton(_('Add child page'), reverse('wagtailadmin_pages:add_subpage', args=[page.id]), priority=40)

    yield ButtonWithDropdownFromHook(
        _('More'),
        hook_name='register_page_listing_more_buttons',
        page=page,
        page_perms=page_perms,
        is_parent=is_parent,
        attrs={'target': '_blank'}, priority=50)


@hooks.register('register_page_listing_more_buttons')
def page_listing_more_buttons(page, page_perms, is_parent=False):
    if page_perms.can_move():
        yield Button(_('Move'), reverse('wagtailadmin_pages:move', args=[page.id]), priority=10)
    if not page.is_root():
        yield Button(_('Copy'), reverse('wagtailadmin_pages:copy', args=[page.id]), priority=20)
    if page_perms.can_delete():
        yield Button(_('Delete'), reverse('wagtailadmin_pages:delete', args=[page.id]), priority=30)
    if page_perms.can_unpublish():
        yield Button(_('Unpublish'), reverse('wagtailadmin_pages:unpublish', args=[page.id]), priority=40)
