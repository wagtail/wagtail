from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.menu import MenuItem, SubmenuMenuItem, settings_menu
from wagtail.wagtailadmin.navigation import get_explorable_root_page
from wagtail.wagtailadmin.search import SearchArea
from wagtail.wagtailadmin.utils import user_has_any_page_permission
from wagtail.wagtailadmin.viewsets import viewsets
from wagtail.wagtailadmin.widgets import Button, ButtonWithDropdownFromHook, PageListingButton
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.permissions import collection_permission_policy


class ExplorerMenuItem(MenuItem):
    template = 'wagtailadmin/shared/explorer_menu_item.html'

    def is_shown(self, request):
        return user_has_any_page_permission(request.user)

    def get_context(self, request):
        context = super(ExplorerMenuItem, self).get_context(request)
        start_page = get_explorable_root_page(request.user)

        if start_page:
            context['start_page_id'] = start_page.id

        return context


@hooks.register('register_admin_menu_item')
def register_explorer_menu_item():
    return ExplorerMenuItem(
        _('Pages'), reverse('wagtailadmin_explore_root'),
        name='explorer',
        classnames='icon icon-folder-open-inverse',
        order=100)


class SettingsMenuItem(SubmenuMenuItem):
    template = 'wagtailadmin/shared/menu_settings_menu_item.html'


@hooks.register('register_admin_menu_item')
def register_settings_menu():
    return SettingsMenuItem(
        _('Settings'), settings_menu, classnames='icon icon-cogs', order=10000)


@hooks.register('register_permissions')
def register_permissions():
    return Permission.objects.filter(content_type__app_label='wagtailadmin', codename='access_admin')


class PageSearchArea(SearchArea):
    def __init__(self):
        super(PageSearchArea, self).__init__(
            _('Pages'), reverse('wagtailadmin_pages:search'),
            name='pages',
            classnames='icon icon-folder-open-inverse',
            order=100)

    def is_shown(self, request):
        return user_has_any_page_permission(request.user)


@hooks.register('register_admin_search_area')
def register_pages_search_area():
    return PageSearchArea()


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
        yield PageListingButton(
            _('Edit'),
            reverse('wagtailadmin_pages:edit', args=[page.id]),
            attrs={'title': _("Edit '{title}'").format(title=page.get_admin_display_title())},
            priority=10
        )
    if page.has_unpublished_changes:
        yield PageListingButton(
            _('View draft'),
            reverse('wagtailadmin_pages:view_draft', args=[page.id]),
            attrs={'title': _("Preview draft version of '{title}'").format(title=page.get_admin_display_title()), 'target': '_blank'},
            priority=20
        )
    if page.live and page.url:
        yield PageListingButton(
            _('View live'),
            page.url,
            attrs={'target': "_blank", 'title': _("View live version of '{title}'").format(title=page.get_admin_display_title())},
            priority=30
        )
    if page_perms.can_add_subpage():
        if is_parent:
            yield Button(
                _('Add child page'),
                reverse('wagtailadmin_pages:add_subpage', args=[page.id]),
                attrs={'title': _("Add a child page to '{title}' ").format(title=page.get_admin_display_title())},
                classes={'button', 'button-small', 'bicolor', 'icon', 'white', 'icon-plus'},
                priority=40
            )
        else:
            yield PageListingButton(
                _('Add child page'),
                reverse('wagtailadmin_pages:add_subpage', args=[page.id]),
                attrs={'title': _("Add a child page to '{title}' ").format(title=page.get_admin_display_title())},
                priority=40
            )

    yield ButtonWithDropdownFromHook(
        _('More'),
        hook_name='register_page_listing_more_buttons',
        page=page,
        page_perms=page_perms,
        is_parent=is_parent,
        attrs={'target': '_blank', 'title': _("View more options for '{title}'").format(title=page.get_admin_display_title())},
        priority=50
    )


@hooks.register('register_page_listing_more_buttons')
def page_listing_more_buttons(page, page_perms, is_parent=False):
    if page_perms.can_move():
        yield Button(
            _('Move'),
            reverse('wagtailadmin_pages:move', args=[page.id]),
            attrs={"title": _("Move page '{title}'").format(title=page.get_admin_display_title())},
            priority=10
        )
    if not page.is_root():
        yield Button(
            _('Copy'),
            reverse('wagtailadmin_pages:copy', args=[page.id]),
            attrs={'title': _("Copy page '{title}'").format(title=page.get_admin_display_title())},
            priority=20
        )
    if page_perms.can_delete():
        yield Button(
            _('Delete'),
            reverse('wagtailadmin_pages:delete', args=[page.id]),
            attrs={'title': _("Delete page '{title}'").format(title=page.get_admin_display_title())},
            priority=30
        )
    if page_perms.can_unpublish():
        yield Button(
            _('Unpublish'),
            reverse('wagtailadmin_pages:unpublish', args=[page.id]),
            attrs={'title': _("Unpublish page '{title}'").format(title=page.get_admin_display_title())},
            priority=40
        )
    if not page.is_root():
        yield Button(
            _('Revisions'),
            reverse('wagtailadmin_pages:revisions_index', args=[page.id]),
            attrs={'title': _("View revision history for '{title}'").format(title=page.get_admin_display_title())},
            priority=50
        )


@hooks.register('register_admin_urls')
def register_viewsets_urls():
    viewsets.populate()
    return viewsets.get_urlpatterns()
