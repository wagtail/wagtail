from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from draftjs_exporter.dom import DOM

import wagtail.admin.rich_text.editors.draftail.features as draftail_features
from wagtail.admin.menu import MenuItem, SubmenuMenuItem, settings_menu
from wagtail.admin.navigation import get_explorable_root_page
from wagtail.admin.rich_text import (
    HalloFormatPlugin, HalloHeadingPlugin, HalloListPlugin, HalloPlugin)
from wagtail.admin.rich_text.converters.contentstate import link_entity
from wagtail.admin.rich_text.converters.editor_html import LinkTypeRule, WhitelistRule
from wagtail.admin.rich_text.converters.html_to_contentstate import (
    BlockElementHandler, ExternalLinkElementHandler, HorizontalRuleHandler,
    InlineStyleElementHandler, ListElementHandler, ListItemElementHandler, PageLinkElementHandler)
from wagtail.admin.search import SearchArea
from wagtail.admin.utils import (
    get_available_admin_languages, get_available_admin_time_zones,
    user_has_any_page_permission)
from wagtail.admin.views.account import password_management_enabled
from wagtail.admin.viewsets import viewsets
from wagtail.admin.widgets import Button, ButtonWithDropdownFromHook, PageListingButton
from wagtail.core import hooks
from wagtail.core.models import UserPagePermissionsProxy
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
            attrs={'title': _("Preview draft version of '{title}'").format(title=page.get_admin_display_title()), 'target': '_blank', 'rel': 'noopener noreferrer'},
            priority=20
        )
    if page.live and page.url:
        yield PageListingButton(
            _('View live'),
            page.url,
            attrs={'target': "_blank", 'rel': 'noopener noreferrer', 'title': _("View live version of '{title}'").format(title=page.get_admin_display_title())},
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
        attrs={'target': '_blank', 'rel': 'noopener noreferrer', 'title': _("View more options for '{title}'").format(title=page.get_admin_display_title())},
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
    if page_perms.can_copy():
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
    if page_perms.can_view_revisions():
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


@hooks.register('register_account_menu_item')
def register_account_set_profile_picture(request):
    return {
        'url': reverse('wagtailadmin_account_change_avatar'),
        'label': _('Set profile picture'),
        'help_text': _("Change your profile picture")
    }


@hooks.register('register_account_menu_item')
def register_account_change_email(request):
    return {
        'url': reverse('wagtailadmin_account_change_email'),
        'label': _('Change email'),
        'help_text': _('Change the email address linked to your account.'),
    }


@hooks.register('register_account_menu_item')
def register_account_change_password(request):
    if password_management_enabled() and request.user.has_usable_password():
        return {
            'url': reverse('wagtailadmin_account_change_password'),
            'label': _('Change password'),
            'help_text': _('Change the password you use to log in.'),
        }


@hooks.register('register_account_menu_item')
def register_account_notification_preferences(request):
    user_perms = UserPagePermissionsProxy(request.user)
    if user_perms.can_edit_pages() or user_perms.can_publish_pages():
        return {
            'url': reverse('wagtailadmin_account_notification_preferences'),
            'label': _('Notification preferences'),
            'help_text': _('Choose which email notifications to receive.'),
        }


@hooks.register('register_account_menu_item')
def register_account_preferred_language_preferences(request):
    if len(get_available_admin_languages()) > 1:
        return {
            'url': reverse('wagtailadmin_account_language_preferences'),
            'label': _('Language preferences'),
            'help_text': _('Choose the language you want to use here.'),
        }


@hooks.register('register_account_menu_item')
def register_account_current_time_zone(request):
    if len(get_available_admin_time_zones()) > 1:
        return {
            'url': reverse('wagtailadmin_account_current_time_zone'),
            'label': _('Current Time Zone'),
            'help_text': _('Choose your current time zone.'),
        }


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
            js=[
                'wagtailadmin/js/page-chooser-modal.js',
                'wagtailadmin/js/hallo-plugins/hallo-wagtaillink.js',
            ],
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

    headings_elements = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    headings_order_start = HalloHeadingPlugin.default_order + 1
    for order, element in enumerate(headings_elements, start=headings_order_start):
        features.register_editor_plugin(
            'hallo', element, HalloHeadingPlugin(element=element, order=order)
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
    features.register_converter_rule('contentstate', 'hr', {
        'from_database_format': {
            'hr': HorizontalRuleHandler(),
        },
        'to_database_format': {
            'entity_decorators': {'HORIZONTAL_RULE': lambda props: DOM.create_element('hr')}
        }
    })

    features.register_editor_plugin(
        'draftail', 'h1', draftail_features.BlockFeature({
            'label': 'H1',
            'type': 'header-one',
            'description': ugettext('Heading {level}').format(level=1),
        })
    )
    features.register_converter_rule('contentstate', 'h1', {
        'from_database_format': {
            'h1': BlockElementHandler('header-one'),
        },
        'to_database_format': {
            'block_map': {'header-one': 'h1'}
        }
    })
    features.register_editor_plugin(
        'draftail', 'h2', draftail_features.BlockFeature({
            'label': 'H2',
            'type': 'header-two',
            'description': ugettext('Heading {level}').format(level=2),
        })
    )
    features.register_converter_rule('contentstate', 'h2', {
        'from_database_format': {
            'h2': BlockElementHandler('header-two'),
        },
        'to_database_format': {
            'block_map': {'header-two': 'h2'}
        }
    })
    features.register_editor_plugin(
        'draftail', 'h3', draftail_features.BlockFeature({
            'label': 'H3',
            'type': 'header-three',
            'description': ugettext('Heading {level}').format(level=3),
        })
    )
    features.register_converter_rule('contentstate', 'h3', {
        'from_database_format': {
            'h3': BlockElementHandler('header-three'),
        },
        'to_database_format': {
            'block_map': {'header-three': 'h3'}
        }
    })
    features.register_editor_plugin(
        'draftail', 'h4', draftail_features.BlockFeature({
            'label': 'H4',
            'type': 'header-four',
            'description': ugettext('Heading {level}').format(level=4),
        })
    )
    features.register_converter_rule('contentstate', 'h4', {
        'from_database_format': {
            'h4': BlockElementHandler('header-four'),
        },
        'to_database_format': {
            'block_map': {'header-four': 'h4'}
        }
    })
    features.register_editor_plugin(
        'draftail', 'h5', draftail_features.BlockFeature({
            'label': 'H5',
            'type': 'header-five',
            'description': ugettext('Heading {level}').format(level=5),
        })
    )
    features.register_converter_rule('contentstate', 'h5', {
        'from_database_format': {
            'h5': BlockElementHandler('header-five'),
        },
        'to_database_format': {
            'block_map': {'header-five': 'h5'}
        }
    })
    features.register_editor_plugin(
        'draftail', 'h6', draftail_features.BlockFeature({
            'label': 'H6',
            'type': 'header-six',
            'description': ugettext('Heading {level}').format(level=6),
        })
    )
    features.register_converter_rule('contentstate', 'h6', {
        'from_database_format': {
            'h6': BlockElementHandler('header-six'),
        },
        'to_database_format': {
            'block_map': {'header-six': 'h6'}
        }
    })
    features.register_editor_plugin(
        'draftail', 'ul', draftail_features.BlockFeature({
            'type': 'unordered-list-item',
            'icon': 'list-ul',
            'description': ugettext('Bulleted list'),
        })
    )
    features.register_converter_rule('contentstate', 'ul', {
        'from_database_format': {
            'ul': ListElementHandler('unordered-list-item'),
            'li': ListItemElementHandler(),
        },
        'to_database_format': {
            'block_map': {'unordered-list-item': {'element': 'li', 'wrapper': 'ul'}}
        }
    })
    features.register_editor_plugin(
        'draftail', 'ol', draftail_features.BlockFeature({
            'type': 'ordered-list-item',
            'icon': 'list-ol',
            'description': ugettext('Numbered list'),
        })
    )
    features.register_converter_rule('contentstate', 'ol', {
        'from_database_format': {
            'ol': ListElementHandler('ordered-list-item'),
            'li': ListItemElementHandler(),
        },
        'to_database_format': {
            'block_map': {'ordered-list-item': {'element': 'li', 'wrapper': 'ol'}}
        }
    })

    features.register_editor_plugin(
        'draftail', 'bold', draftail_features.InlineStyleFeature({
            'type': 'BOLD',
            'icon': 'bold',
            'description': ugettext('Bold'),
        })
    )
    features.register_converter_rule('contentstate', 'bold', {
        'from_database_format': {
            'b': InlineStyleElementHandler('BOLD'),
            'strong': InlineStyleElementHandler('BOLD'),
        },
        'to_database_format': {
            'style_map': {'BOLD': 'b'}
        }
    })
    features.register_editor_plugin(
        'draftail', 'italic', draftail_features.InlineStyleFeature({
            'type': 'ITALIC',
            'icon': 'italic',
            'description': ugettext('Italic'),
        })
    )
    features.register_converter_rule('contentstate', 'italic', {
        'from_database_format': {
            'i': InlineStyleElementHandler('ITALIC'),
            'em': InlineStyleElementHandler('ITALIC'),
        },
        'to_database_format': {
            'style_map': {'ITALIC': 'i'}
        }
    })

    features.register_editor_plugin(
        'draftail', 'link', draftail_features.EntityFeature({
            'type': 'LINK',
            'icon': 'link',
            'description': ugettext('Link'),
            # We want to enforce constraints on which links can be pasted into rich text.
            # Keep only the attributes Wagtail needs.
            'attributes': ['url', 'id', 'parentId'],
            'whitelist': {
                # Keep pasted links with http/https protocol, and not-pasted links (href = undefined).
                'href': "^(http:|https:|undefined$)",
            }
        }, js=[
            'wagtailadmin/js/page-chooser-modal.js',
        ])
    )
    features.register_converter_rule('contentstate', 'link', {
        'from_database_format': {
            'a[href]': ExternalLinkElementHandler('LINK'),
            'a[linktype="page"]': PageLinkElementHandler('LINK'),
        },
        'to_database_format': {
            'entity_decorators': {'LINK': link_entity}
        }
    })
