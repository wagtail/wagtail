from django.conf import settings
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from draftjs_exporter.dom import DOM

import wagtail.admin.rich_text.editors.draftail.features as draftail_features

from wagtail import __version__
from wagtail.admin.admin_url_finder import ModelAdminURLFinder, register_admin_url_finder
from wagtail.admin.auth import user_has_any_page_permission
from wagtail.admin.forms.collections import GroupCollectionManagementPermissionFormSet
from wagtail.admin.menu import MenuItem, SubmenuMenuItem, reports_menu, settings_menu
from wagtail.admin.navigation import get_explorable_root_page
from wagtail.admin.rich_text import (
    HalloFormatPlugin, HalloHeadingPlugin, HalloListPlugin, HalloPlugin)
from wagtail.admin.rich_text.converters.contentstate import link_entity
from wagtail.admin.rich_text.converters.editor_html import (
    LinkTypeRule, PageLinkHandler, WhitelistRule)
from wagtail.admin.rich_text.converters.html_to_contentstate import (
    BlockElementHandler, ExternalLinkElementHandler, HorizontalRuleHandler,
    InlineStyleElementHandler, ListElementHandler, ListItemElementHandler, PageLinkElementHandler)
from wagtail.admin.search import SearchArea
from wagtail.admin.site_summary import PagesSummaryItem
from wagtail.admin.ui.sidebar import PageExplorerMenuItem as PageExplorerMenuItemComponent
from wagtail.admin.ui.sidebar import SubMenuItem as SubMenuItemComponent
from wagtail.admin.views.pages.bulk_actions import (
    DeleteBulkAction, MoveBulkAction, PublishBulkAction, UnpublishBulkAction)
from wagtail.admin.viewsets import viewsets
from wagtail.admin.widgets import Button, ButtonWithDropdownFromHook, PageListingButton
from wagtail.core import hooks
from wagtail.core.models import Collection, Page, Task, UserPagePermissionsProxy, Workflow
from wagtail.core.permissions import (
    collection_permission_policy, task_permission_policy, workflow_permission_policy)
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

    def render_component(self, request):
        start_page = get_explorable_root_page(request.user)

        if start_page:
            return PageExplorerMenuItemComponent(self.name, self.label, self.url, start_page.id, icon_name=self.icon_name, classnames=self.classnames)
        else:
            return super().render_component(request)


@hooks.register('register_admin_menu_item')
def register_explorer_menu_item():
    return ExplorerMenuItem(
        _('Pages'), reverse('wagtailadmin_explore_root'),
        name='explorer',
        icon_name='folder-open-inverse',
        order=100)


class SettingsMenuItem(SubmenuMenuItem):
    template = 'wagtailadmin/shared/menu_settings_menu_item.html'

    def render_component(self, request):
        return SubMenuItemComponent(
            self.name,
            self.label,
            self.menu.render_component(request),
            icon_name=self.icon_name,
            classnames=self.classnames,
            footer_text="Wagtail v." + __version__
        )


@hooks.register('register_admin_menu_item')
def register_settings_menu():
    return SettingsMenuItem(
        _('Settings'),
        settings_menu,
        icon_name='cogs',
        order=10000)


@hooks.register('register_permissions')
def register_permissions():
    return Permission.objects.filter(content_type__app_label='wagtailadmin', codename='access_admin')


class PageSearchArea(SearchArea):
    def __init__(self):
        super().__init__(
            _('Pages'), reverse('wagtailadmin_pages:search'),
            name='pages',
            icon_name='folder-open-inverse',
            order=100)

    def is_shown(self, request):
        return user_has_any_page_permission(request.user)


@hooks.register('register_admin_search_area')
def register_pages_search_area():
    return PageSearchArea()


@hooks.register('register_group_permission_panel')
def register_collection_permissions_panel():
    return GroupCollectionManagementPermissionFormSet


class CollectionsMenuItem(MenuItem):
    def is_shown(self, request):
        return collection_permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


@hooks.register('register_settings_menu_item')
def register_collections_menu_item():
    return CollectionsMenuItem(_('Collections'), reverse('wagtailadmin_collections:index'), icon_name='folder-open-1', order=700)


class WorkflowsMenuItem(MenuItem):
    def is_shown(self, request):
        if not getattr(settings, 'WAGTAIL_WORKFLOW_ENABLED', True):
            return False

        return workflow_permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


class WorkflowTasksMenuItem(MenuItem):
    def is_shown(self, request):
        if not getattr(settings, 'WAGTAIL_WORKFLOW_ENABLED', True):
            return False

        return task_permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


@hooks.register('register_settings_menu_item')
def register_workflows_menu_item():
    return WorkflowsMenuItem(_('Workflows'), reverse('wagtailadmin_workflows:index'), icon_name='tasks', order=100)


@hooks.register('register_settings_menu_item')
def register_workflow_tasks_menu_item():
    return WorkflowTasksMenuItem(_('Workflow tasks'), reverse('wagtailadmin_workflows:task_index'), icon_name='thumbtack', order=150)


@hooks.register('register_page_listing_buttons')
def page_listing_buttons(page, page_perms, is_parent=False, next_url=None):
    if page_perms.can_edit():
        yield PageListingButton(
            _('Edit'),
            reverse('wagtailadmin_pages:edit', args=[page.id]),
            attrs={'aria-label': _("Edit '%(title)s'") % {'title': page.get_admin_display_title()}},
            priority=10
        )
    if page.has_unpublished_changes and page.is_previewable():
        yield PageListingButton(
            _('View draft'),
            reverse('wagtailadmin_pages:view_draft', args=[page.id]),
            attrs={
                'aria-label': _("Preview draft version of '%(title)s'") % {'title': page.get_admin_display_title()},
                'rel': 'noopener noreferrer'
            },
            priority=20
        )
    if page.live and page.url:
        yield PageListingButton(
            _('View live'),
            page.url,
            attrs={
                'rel': 'noopener noreferrer',
                'aria-label': _("View live version of '%(title)s'") % {'title': page.get_admin_display_title()},
            },
            priority=30
        )
    if page_perms.can_add_subpage():
        if is_parent:
            yield Button(
                _('Add child page'),
                reverse('wagtailadmin_pages:add_subpage', args=[page.id]),
                attrs={
                    'aria-label': _("Add a child page to '%(title)s' ") % {'title': page.get_admin_display_title()},
                },
                classes={'button', 'button-small', 'bicolor', 'icon', 'white', 'icon-plus'},
                priority=40
            )
        else:
            yield PageListingButton(
                _('Add child page'),
                reverse('wagtailadmin_pages:add_subpage', args=[page.id]),
                attrs={'aria-label': _("Add a child page to '%(title)s' ") % {'title': page.get_admin_display_title()}},
                priority=40
            )

    yield ButtonWithDropdownFromHook(
        _('More'),
        hook_name='register_page_listing_more_buttons',
        page=page,
        page_perms=page_perms,
        is_parent=is_parent,
        next_url=next_url,
        attrs={
            'target': '_blank', 'rel': 'noopener noreferrer',
            'title': _("View more options for '%(title)s'") % {'title': page.get_admin_display_title()}
        },
        priority=50
    )


@hooks.register('register_page_listing_more_buttons')
def page_listing_more_buttons(page, page_perms, is_parent=False, next_url=None):
    if page_perms.can_move():
        yield Button(
            _('Move'),
            reverse('wagtailadmin_pages:move', args=[page.id]),
            attrs={"title": _("Move page '%(title)s'") % {'title': page.get_admin_display_title()}},
            priority=10
        )
    if page_perms.can_copy():
        url = reverse('wagtailadmin_pages:copy', args=[page.id])
        if next_url:
            url += '?' + urlencode({'next': next_url})

        yield Button(
            _('Copy'),
            url,
            attrs={'title': _("Copy page '%(title)s'") % {'title': page.get_admin_display_title()}},
            priority=20
        )
    if page_perms.can_delete():
        url = reverse('wagtailadmin_pages:delete', args=[page.id])

        # After deleting the page, it is impossible to redirect to it.
        if next_url == reverse('wagtailadmin_explore', args=[page.id]):
            next_url = None

        if next_url:
            url += '?' + urlencode({'next': next_url})

        yield Button(
            _('Delete'),
            url,
            attrs={'title': _("Delete page '%(title)s'") % {'title': page.get_admin_display_title()}},
            priority=30
        )
    if page_perms.can_unpublish():
        url = reverse('wagtailadmin_pages:unpublish', args=[page.id])
        if next_url:
            url += '?' + urlencode({'next': next_url})

        yield Button(
            _('Unpublish'),
            url,
            attrs={'title': _("Unpublish page '%(title)s'") % {'title': page.get_admin_display_title()}},
            priority=40
        )
    if page_perms.can_view_revisions():
        yield Button(
            _('History'),
            reverse('wagtailadmin_pages:history', args=[page.id]),
            attrs={'title': _("View page history for '%(title)s'") % {'title': page.get_admin_display_title()}},
            priority=50
        )

    if is_parent:
        yield Button(
            _('Sort menu order'),
            '?ordering=ord',
            attrs={'title': _("Change ordering of child pages of '%(title)s'") % {'title': page.get_admin_display_title()}},
            priority=60
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
            'description': gettext('Heading %(level)d') % {'level': 1},
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
            'description': gettext('Heading %(level)d') % {'level': 2},
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
            'description': gettext('Heading %(level)d') % {'level': 3},
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
            'description': gettext('Heading %(level)d') % {'level': 4},
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
            'description': gettext('Heading %(level)d') % {'level': 5},
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
            'description': gettext('Heading %(level)d') % {'level': 6},
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
            'description': gettext('Bulleted list'),
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
            'description': gettext('Numbered list'),
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
        'draftail', 'blockquote', draftail_features.BlockFeature({
            'type': 'blockquote',
            'icon': 'openquote',
            'description': gettext('Blockquote'),
        })
    )
    features.register_converter_rule('contentstate', 'blockquote', {
        'from_database_format': {
            'blockquote': BlockElementHandler('blockquote'),
        },
        'to_database_format': {
            'block_map': {'blockquote': 'blockquote'}
        }
    })

    features.register_editor_plugin(
        'draftail', 'bold', draftail_features.InlineStyleFeature({
            'type': 'BOLD',
            'icon': 'bold',
            'description': gettext('Bold'),
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
            'description': gettext('Italic'),
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
            'description': gettext('Link'),
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
    features.register_editor_plugin(
        'draftail', 'superscript', draftail_features.InlineStyleFeature({
            'type': 'SUPERSCRIPT',
            'icon': 'superscript',
            'description': gettext('Superscript'),
        })
    )
    features.register_converter_rule('contentstate', 'superscript', {
        'from_database_format': {
            'sup': InlineStyleElementHandler('SUPERSCRIPT'),
        },
        'to_database_format': {
            'style_map': {'SUPERSCRIPT': 'sup'}
        }
    })
    features.register_editor_plugin(
        'draftail', 'subscript', draftail_features.InlineStyleFeature({
            'type': 'SUBSCRIPT',
            'icon': 'subscript',
            'description': gettext('Subscript'),
        })
    )
    features.register_converter_rule('contentstate', 'subscript', {
        'from_database_format': {
            'sub': InlineStyleElementHandler('SUBSCRIPT'),
        },
        'to_database_format': {
            'style_map': {'SUBSCRIPT': 'sub'}
        }
    })
    features.register_editor_plugin(
        'draftail', 'strikethrough', draftail_features.InlineStyleFeature({
            'type': 'STRIKETHROUGH',
            'icon': 'strikethrough',
            'description': gettext('Strikethrough'),
        })
    )
    features.register_converter_rule('contentstate', 'strikethrough', {
        'from_database_format': {
            's': InlineStyleElementHandler('STRIKETHROUGH'),
        },
        'to_database_format': {
            'style_map': {'STRIKETHROUGH': 's'}
        }
    })
    features.register_editor_plugin(
        'draftail', 'code', draftail_features.InlineStyleFeature({
            'type': 'CODE',
            'icon': 'code',
            'description': gettext('Code'),
        })
    )
    features.register_converter_rule('contentstate', 'code', {
        'from_database_format': {
            'code': InlineStyleElementHandler('CODE'),
        },
        'to_database_format': {
            'style_map': {'CODE': 'code'}
        }
    })


class ReportsMenuItem(SubmenuMenuItem):
    template = 'wagtailadmin/shared/menu_submenu_item.html'


class LockedPagesMenuItem(MenuItem):
    def is_shown(self, request):
        return UserPagePermissionsProxy(request.user).can_remove_locks()


class WorkflowReportMenuItem(MenuItem):
    def is_shown(self, request):
        return getattr(settings, 'WAGTAIL_WORKFLOW_ENABLED', True)


class SiteHistoryReportMenuItem(MenuItem):
    def is_shown(self, request):
        return UserPagePermissionsProxy(request.user).explorable_pages().exists()


@hooks.register('register_reports_menu_item')
def register_locked_pages_menu_item():
    return LockedPagesMenuItem(_('Locked Pages'), reverse('wagtailadmin_reports:locked_pages'), icon_name='lock', order=700)


@hooks.register('register_reports_menu_item')
def register_workflow_report_menu_item():
    return WorkflowReportMenuItem(_('Workflows'), reverse('wagtailadmin_reports:workflow'), icon_name='tasks', order=800)


@hooks.register('register_reports_menu_item')
def register_workflow_tasks_report_menu_item():
    return WorkflowReportMenuItem(_('Workflow tasks'), reverse('wagtailadmin_reports:workflow_tasks'), icon_name='thumbtack', order=900)


@hooks.register('register_reports_menu_item')
def register_site_history_report_menu_item():
    return SiteHistoryReportMenuItem(_('Site history'), reverse('wagtailadmin_reports:site_history'), icon_name='history', order=1000)


@hooks.register('register_admin_menu_item')
def register_reports_menu():
    return ReportsMenuItem(
        _('Reports'), reports_menu, icon_name='site', order=9000)


@hooks.register('register_icons')
def register_icons(icons):
    for icon in [
        'angle-double-left.svg',
        'angle-double-right.svg',
        'arrow-down-big.svg',
        'arrow-down.svg',
        'arrow-left.svg',
        'arrow-right.svg',
        'arrow-up-big.svg',
        'arrow-up.svg',
        'arrows-up-down.svg',
        'bars.svg',
        'bin.svg',
        'bold.svg',
        'chain-broken.svg',
        'check.svg',
        'chevron-down.svg',
        'clipboard-list.svg',
        'code.svg',
        'cog.svg',
        'cogs.svg',
        'collapse-down.svg',
        'collapse-up.svg',
        'comment.svg',
        'comment-add.svg',
        'comment-add-reversed.svg',
        'comment-large.svg',
        'comment-large-outline.svg',
        'comment-large-reversed.svg',
        'cross.svg',
        'date.svg',
        'doc-empty-inverse.svg',
        'doc-empty.svg',
        'doc-full-inverse.svg',
        'doc-full.svg',  # aka file-text-alt
        'download-alt.svg',
        'download.svg',
        'draft.svg',
        'duplicate.svg',
        'edit.svg',
        'ellipsis-v.svg',
        'error.svg',
        'folder-inverse.svg',
        'folder-open-1.svg',
        'folder-open-inverse.svg',
        'folder.svg',
        'form.svg',
        'grip.svg',
        'group.svg',
        'help.svg',
        'history.svg',
        'home.svg',
        'horizontalrule.svg',
        'image.svg',  # aka picture
        'info-circle.svg',
        'italic.svg',
        'link.svg',
        'link-external.svg',
        'list-ol.svg',
        'list-ul.svg',
        'lock-open.svg',
        'lock.svg',
        'login.svg',
        'logout.svg',
        'mail.svg',
        'media.svg',
        'no-view.svg',
        'openquote.svg',
        'order-down.svg',
        'order-up.svg',
        'order.svg',
        'password.svg',
        'pick.svg',
        'pilcrow.svg',
        'placeholder.svg',  # aka marquee
        'plus-inverse.svg',
        'plus.svg',
        'radio-empty.svg',
        'radio-full.svg',
        'redirect.svg',
        'repeat.svg',
        'reset.svg',
        'resubmit.svg',
        'search.svg',
        'site.svg',
        'snippet.svg',
        'spinner.svg',
        'strikethrough.svg',
        'success.svg',
        'subscript.svg',
        'superscript.svg',
        'table.svg',
        'tag.svg',
        'tasks.svg',
        'thumbtack.svg',
        'tick-inverse.svg',
        'tick.svg',
        'time.svg',
        'title.svg',
        'undo.svg',
        'uni52.svg',  # Is this a redundant icon?
        'upload.svg',
        'user.svg',
        'view.svg',
        'wagtail-inverse.svg',
        'wagtail.svg',
        'warning.svg',
    ]:
        icons.append('wagtailadmin/icons/{}'.format(icon))
    return icons


@hooks.register('construct_homepage_summary_items')
def add_pages_summary_item(request, items):
    items.insert(0, PagesSummaryItem(request))


class PageAdminURLFinder:
    def __init__(self, user):
        self.page_perms = user and UserPagePermissionsProxy(user)

    def get_edit_url(self, instance):
        if self.page_perms and not self.page_perms.for_page(instance).can_edit():
            return None
        else:
            return reverse('wagtailadmin_pages:edit', args=(instance.pk, ))


register_admin_url_finder(Page, PageAdminURLFinder)


class CollectionAdminURLFinder(ModelAdminURLFinder):
    permission_policy = collection_permission_policy
    edit_url_name = 'wagtailadmin_collections:edit'


register_admin_url_finder(Collection, CollectionAdminURLFinder)


class WorkflowAdminURLFinder(ModelAdminURLFinder):
    permission_policy = workflow_permission_policy
    edit_url_name = 'wagtailadmin_workflows:edit'


register_admin_url_finder(Workflow, WorkflowAdminURLFinder)


class WorkflowTaskAdminURLFinder(ModelAdminURLFinder):
    permission_policy = task_permission_policy
    edit_url_name = 'wagtailadmin_workflows:edit_task'


register_admin_url_finder(Task, WorkflowTaskAdminURLFinder)


for action_class in [DeleteBulkAction, MoveBulkAction, PublishBulkAction, UnpublishBulkAction]:
    hooks.register('register_bulk_action', action_class)
