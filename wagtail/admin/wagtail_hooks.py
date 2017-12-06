from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from draftjs_exporter.constants import BLOCK_TYPES, ENTITY_TYPES, INLINE_STYLES

from wagtail.admin.menu import MenuItem, SubmenuMenuItem, settings_menu
from wagtail.admin.navigation import get_explorable_root_page
from wagtail.admin.rich_text import (
    HalloFormatPlugin, HalloHeadingPlugin, HalloListPlugin, HalloPlugin)
from wagtail.admin.rich_text.converters.editor_html import LinkTypeRule, WhitelistRule
import wagtail.admin.rich_text.editors.draftail.features as draftail_features
from wagtail.admin.search import SearchArea
from wagtail.admin.utils import user_has_any_page_permission
from wagtail.admin.viewsets import viewsets
from wagtail.admin.widgets import Button, ButtonWithDropdownFromHook, PageListingButton
from wagtail.core import hooks
from wagtail.core.permissions import collection_permission_policy
from wagtail.core.rich_text.pages import PageLinkHandler
from wagtail.core.whitelist import allow_without_attributes, attribute_rule, check_url


class ExplorerMenuItem(MenuItem):
    template = 'wagtailadmin/shared/explorer_menu_item.html'

    def is_shown(self, request):
        return user_has_any_page_permission(request.user)

    def get_context(self, request):
        context = super().get_context(request)
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
        super().__init__(
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


@hooks.register('register_rich_text_features')
def register_core_features(features):
    # Hallo.js
    features.register_editor_plugin(
        'hallo', 'hr',
        HalloPlugin(
            name='hallohr',
            js=['wagtailadmin/js/hallo-plugins/hallo-hr.js'],
            order=45,
        )
    )
    features.register_converter_rule('editorhtml', 'hr', [
        WhitelistRule('hr', allow_without_attributes)
    ])

    features.register_editor_plugin(
        'hallo', 'link',
        HalloPlugin(
            name='hallowagtaillink',
            js=['wagtailadmin/js/hallo-plugins/hallo-wagtaillink.js'],
        )
    )
    features.register_converter_rule('editorhtml', 'link', [
        WhitelistRule('a', attribute_rule({'href': check_url})),
        LinkTypeRule('page', PageLinkHandler),
    ])

    features.register_editor_plugin(
        'hallo', 'bold', HalloFormatPlugin(format_name='bold')
    )
    features.register_converter_rule('editorhtml', 'bold', [
        WhitelistRule('b', allow_without_attributes),
        WhitelistRule('strong', allow_without_attributes),
    ])

    features.register_editor_plugin(
        'hallo', 'italic', HalloFormatPlugin(format_name='italic')
    )
    features.register_converter_rule('editorhtml', 'italic', [
        WhitelistRule('i', allow_without_attributes),
        WhitelistRule('em', allow_without_attributes),
    ])

    for element in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        features.register_editor_plugin(
            'hallo', element, HalloHeadingPlugin(element=element)
        )
        features.register_converter_rule('editorhtml', element, [
            WhitelistRule(element, allow_without_attributes)
        ])

    features.register_editor_plugin(
        'hallo', 'ol', HalloListPlugin(list_type='ordered')
    )
    features.register_converter_rule('editorhtml', 'ol', [
        WhitelistRule('ol', allow_without_attributes),
        WhitelistRule('li', allow_without_attributes),
    ])

    features.register_editor_plugin(
        'hallo', 'ul', HalloListPlugin(list_type='unordered')
    )
    features.register_converter_rule('editorhtml', 'ul', [
        WhitelistRule('ul', allow_without_attributes),
        WhitelistRule('li', allow_without_attributes),
    ])

    # Draftail
    features.register_editor_plugin(
        'draftail', 'hr', draftail_features.BooleanFeature('enableHorizontalRule')
    )

    features.register_editor_plugin(
        'draftail', 'br', draftail_features.BooleanFeature('enableLineBreak')
    )

    features.register_editor_plugin(
        'draftail', 'h1', draftail_features.BlockFeature({'label': 'H1', 'type': BLOCK_TYPES.HEADER_ONE})
    )
    features.register_editor_plugin(
        'draftail', 'h2', draftail_features.BlockFeature({'label': 'H2', 'type': BLOCK_TYPES.HEADER_TWO})
    )
    features.register_editor_plugin(
        'draftail', 'h3', draftail_features.BlockFeature({'label': 'H3', 'type': BLOCK_TYPES.HEADER_THREE})
    )
    features.register_editor_plugin(
        'draftail', 'h4', draftail_features.BlockFeature({'label': 'H4', 'type': BLOCK_TYPES.HEADER_FOUR})
    )
    features.register_editor_plugin(
        'draftail', 'h5', draftail_features.BlockFeature({'label': 'H5', 'type': BLOCK_TYPES.HEADER_FIVE})
    )
    features.register_editor_plugin(
        'draftail', 'h6', draftail_features.BlockFeature({'label': 'H6', 'type': BLOCK_TYPES.HEADER_SIX})
    )
    features.register_editor_plugin(
        'draftail', 'ul', draftail_features.BlockFeature({
            'label': 'UL', 'type': BLOCK_TYPES.UNORDERED_LIST_ITEM, 'icon': 'icon-list-ul'
        })
    )
    features.register_editor_plugin(
        'draftail', 'ol', draftail_features.BlockFeature({
            'label': 'OL', 'type': BLOCK_TYPES.ORDERED_LIST_ITEM, 'icon': 'icon-list-ol'
        })
    )

    features.register_editor_plugin(
        'draftail', 'bold', draftail_features.InlineStyleFeature({
            'label': 'Bold', 'type': INLINE_STYLES.BOLD, 'icon': 'icon-bold'
        })
    )
    features.register_editor_plugin(
        'draftail', 'italic', draftail_features.InlineStyleFeature({
            'label': 'Italic', 'type': INLINE_STYLES.ITALIC, 'icon': 'icon-italic'
        })
    )

    features.register_editor_plugin(
        'draftail', 'link', draftail_features.EntityFeature({
            'label': 'Link',
            'type': ENTITY_TYPES.LINK,
            'icon': 'icon-link',
            'source': 'LinkSource',
            'decorator': 'Link',
        })
    )

    features.register_editor_plugin(
        'draftail', 'document-link', draftail_features.EntityFeature({
            'label': 'Document',
            'type': ENTITY_TYPES.DOCUMENT,
            'icon': 'icon-doc-full',
            'source': 'DocumentSource',
            'decorator': 'Document',
        })
    )

    features.register_editor_plugin(
        'draftail', 'image', draftail_features.ImageFeature()
    )

    features.register_editor_plugin(
        'draftail', 'embed', draftail_features.EntityFeature({
            'label': 'Embed',
            'type': ENTITY_TYPES.EMBED,
            'icon': 'icon-media',
            'source': 'EmbedSource',
            'decorator': 'Embed',
        })
    )
