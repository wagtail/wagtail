from __future__ import absolute_import, unicode_literals

from django import forms
from django.contrib.auth.models import Permission
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailadmin.menu import MenuItem, SubmenuMenuItem, settings_menu
from wagtail.wagtailadmin.search import SearchArea
from wagtail.wagtailadmin.widgets import Button, ButtonWithDropdownFromHook, CollectionListingButton, PageListingButton
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.permissions import collection_permission_policy


class ExplorerMenuItem(MenuItem):
    @property
    def media(self):
        return forms.Media(js=[static('wagtailadmin/js/explorer-menu.js')])


@hooks.register('register_admin_menu_item')
def register_explorer_menu_item():
    return ExplorerMenuItem(
        _('Explorer'), reverse('wagtailadmin_explore_root'),
        name='explorer',
        classnames='icon icon-folder-open-inverse dl-trigger',
        attrs={'data-explorer-menu-url': reverse('wagtailadmin_explorer_nav')},
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


@hooks.register('register_collection_listing_buttons')
def collection_listing_buttons(collection, collection_perms, is_parent=False):
    if collection_perms.can_edit():
        yield CollectionListingButton(
            _('Edit'),
            reverse('wagtailadmin_collections:edit', args=(collection.pk, )),
            attrs={'title': _("Edit '{name}'").format(name=collection.name)},
            priority=10,
        )
    if collection_perms.can_add():
        add_child_button = CollectionListingButton(
            _('Add Child'),
            reverse('wagtailadmin_collections:add_child', args=(collection.pk, )),
            attrs={'title': _("Add child collection to '{name}'").format(name=collection.name)},
            priority=20,
        )
        if is_parent:
            add_child_button.classes = {'button', 'button-small', 'bicolor', 'icon', 'white', 'icon-plus'}
        yield add_child_button


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
