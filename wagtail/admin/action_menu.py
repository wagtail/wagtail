"""Handles rendering of the list of actions in the footer of the page create/edit views."""

from django.conf import settings
from django.forms import Media, MediaDefiningClass
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.core import hooks
from wagtail.core.models import UserPagePermissionsProxy


class ActionMenuItem(metaclass=MediaDefiningClass):
    """Defines an item in the actions drop-up on the page creation/edit view"""
    order = 100  # default order index if one is not specified on init
    template = 'wagtailadmin/pages/action_menu/menu_item.html'

    label = ''
    name = None
    classname = ''

    def __init__(self, order=None):
        if order is not None:
            self.order = order

    def is_shown(self, request, context):
        """
        Whether this action should be shown on this request; permission checks etc should go here.
        By default, actions are shown for unlocked pages, hidden for locked pages

        request = the current request object

        context = dictionary containing at least:
            'view' = 'create', 'edit' or 'revisions_revert'
            'page' (if view = 'edit' or 'revisions_revert') = the page being edited
            'parent_page' (if view = 'create') = the parent page of the page being created
            'user_page_permissions' = a UserPagePermissionsProxy for the current user, to test permissions against
        """
        return (context['view'] == 'create' or not context['user_page_permissions'].for_page(context['page']).page_locked())

    def get_context(self, request, parent_context):
        """Defines context for the template, overridable to use more data"""
        context = parent_context.copy()
        context.update({
            'label': self.label,
            'url': self.get_url(request, context),
            'name': self.name,
            'classname': self.classname,
        })
        return context

    def get_url(self, request, context):
        return None

    def render_html(self, request, parent_context):
        context = self.get_context(request, parent_context)
        return render_to_string(self.template, context, request=request)


class PublishMenuItem(ActionMenuItem):
    label = _("Publish")
    name = 'action-publish'
    template = 'wagtailadmin/pages/action_menu/publish.html'

    def is_shown(self, request, context):
        if context['view'] == 'create':
            return context['user_page_permissions'].for_page(context['parent_page']).can_publish_subpage()
        else:  # view == 'edit' or 'revisions_revert'
            return (
                not context['user_page_permissions'].for_page(context['page']).page_locked()
                and context['user_page_permissions'].for_page(context['page']).can_publish()
            )

    def get_context(self, request, parent_context):
        context = super().get_context(request, parent_context)
        context['is_revision'] = (context['view'] == 'revisions_revert')
        return context


class SubmitForModerationMenuItem(ActionMenuItem):
    label = _("Submit for moderation")
    name = 'action-submit'

    def is_shown(self, request, context):
        WAGTAIL_MODERATION_ENABLED = getattr(settings, 'WAGTAIL_MODERATION_ENABLED', True)
        if not WAGTAIL_MODERATION_ENABLED:
            return False
        elif context['view'] == 'create':
            return context['parent_page'].has_workflow
        elif context['view'] == 'edit':
            permissions = context['user_page_permissions'].for_page(context['page'])
            return permissions.can_submit_for_moderation() and not permissions.page_locked()
        else:  # context == revisions_revert
            return False

    def get_context(self, request, parent_context):
        context = super().get_context(request, parent_context)
        page = context.get('page')
        workflow_state = page.current_workflow_state if page else None
        if workflow_state and workflow_state.status == workflow_state.STATUS_NEEDS_CHANGES:
            context['label'] = _("Resubmit to {}").format(workflow_state.current_task_state.task.name)
        return context


class WorkflowMenuItem(ActionMenuItem):
    template = 'wagtailadmin/pages/action_menu/workflow_menu_item.html'

    def __init__(self, name, label, launch_modal, *args, **kwargs):
        self.name = name
        self.label = label
        self.launch_modal = launch_modal
        super().__init__(*args, **kwargs)

    def get_context(self, request, parent_context):
        context = super().get_context(request, parent_context)
        context['launch_modal'] = self.launch_modal
        context['current_task_state'] = context['page'].current_workflow_task_state
        return context

    def is_shown(self, request, context):
        if context['view'] == 'edit':
            return not context['user_page_permissions'].for_page(context['page']).page_locked()


class RestartWorkflowMenuItem(ActionMenuItem):
    label = _("Restart workflow ")
    name = 'action-restart-workflow'

    def is_shown(self, request, context):
        WAGTAIL_MODERATION_ENABLED = getattr(settings, 'WAGTAIL_MODERATION_ENABLED', True)
        if not WAGTAIL_MODERATION_ENABLED:
            return False
        elif context['view'] == 'edit':
            workflow_state = context['page'].current_workflow_state
            permissions = context['user_page_permissions'].for_page(context['page'])
            return permissions.can_submit_for_moderation() and not permissions.page_locked() and workflow_state and workflow_state.user_can_cancel(request.user)
        else:
            return False


class CancelWorkflowMenuItem(ActionMenuItem):
    label = _("Cancel workflow ")
    name = 'action-cancel-workflow'
    classname = 'no'

    def is_shown(self, request, context):
        if context['view'] == 'edit':
            workflow_state = context['page'].current_workflow_state
            return workflow_state and workflow_state.user_can_cancel(request.user)
        return False


class UnpublishMenuItem(ActionMenuItem):
    label = _("Unpublish")
    name = 'action-unpublish'
    classname = 'no'

    def is_shown(self, request, context):
        return (
            context['view'] == 'edit'
            and not context['user_page_permissions'].for_page(context['page']).page_locked()
            and context['user_page_permissions'].for_page(context['page']).can_unpublish()
        )

    def get_url(self, request, context):
        return reverse('wagtailadmin_pages:unpublish', args=(context['page'].id,))


class DeleteMenuItem(ActionMenuItem):
    name = 'action-delete'
    label = _("Delete")
    classname = 'no'

    def is_shown(self, request, context):
        return (
            context['view'] == 'edit'
            and not context['user_page_permissions'].for_page(context['page']).page_locked()
            and context['user_page_permissions'].for_page(context['page']).can_delete()
        )

    def get_url(self, request, context):
        return reverse('wagtailadmin_pages:delete', args=(context['page'].id,))


class SaveDraftMenuItem(ActionMenuItem):
    name = 'action-save-draft'
    label = _("Save Draft")
    template = 'wagtailadmin/pages/action_menu/save_draft.html'

    def get_context(self, request, parent_context):
        context = super().get_context(request, parent_context)
        context['is_revision'] = (context['view'] == 'revisions_revert')
        return context


class PageLockedMenuItem(ActionMenuItem):
    name = 'action-page-locked'
    label = _("Page locked")
    template = 'wagtailadmin/pages/action_menu/page_locked.html'

    def is_shown(self, request, context):
        return ('page' in context) and context['user_page_permissions'].for_page(context['page']).page_locked()

    def get_context(self, request, parent_context):
        context = super().get_context(request, parent_context)
        context['is_revision'] = (context['view'] == 'revisions_revert')
        return context


BASE_PAGE_ACTION_MENU_ITEMS = None


def _get_base_page_action_menu_items():
    """
    Retrieve the global list of menu items for the page action menu,
    which may then be customised on a per-request basis
    """
    global BASE_PAGE_ACTION_MENU_ITEMS

    if BASE_PAGE_ACTION_MENU_ITEMS is None:
        BASE_PAGE_ACTION_MENU_ITEMS = [
            SaveDraftMenuItem(order=0),
            UnpublishMenuItem(order=10),
            DeleteMenuItem(order=20),
            PublishMenuItem(order=30),
            RestartWorkflowMenuItem(order=40),
            CancelWorkflowMenuItem(order=50),
            SubmitForModerationMenuItem(order=60),
            PageLockedMenuItem(order=10000),
        ]
        for hook in hooks.get_hooks('register_page_action_menu_item'):
            BASE_PAGE_ACTION_MENU_ITEMS.append(hook())

    return BASE_PAGE_ACTION_MENU_ITEMS


class PageActionMenu:
    template = 'wagtailadmin/pages/action_menu/menu.html'

    def __init__(self, request, **kwargs):
        self.request = request
        self.context = kwargs
        self.context['user_page_permissions'] = UserPagePermissionsProxy(self.request.user)

        self.menu_items = []

        page = self.context.get('page')
        if page:
            task = page.current_workflow_task
            if task:
                actions = task.get_actions(page, request.user)
                workflow_menu_items = [WorkflowMenuItem(name, label, launch_modal) for name, label, launch_modal in actions]
                workflow_menu_items = [item for item in workflow_menu_items if item.is_shown(self.request, self.context)]
                self.menu_items.extend(workflow_menu_items)

        self.menu_items.extend([
            menu_item
            for menu_item in _get_base_page_action_menu_items()
            if menu_item.is_shown(self.request, self.context)
        ])

        self.menu_items.sort(key=lambda item: item.order)

        for hook in hooks.get_hooks('construct_page_action_menu'):
            hook(self.menu_items, self.request, self.context)


        try:
            self.default_item = self.menu_items.pop(0)
        except IndexError:
            self.default_item = None

    def render_html(self):
        return render_to_string(self.template, {
            'default_menu_item': self.default_item.render_html(self.request, self.context),
            'show_menu': bool(self.menu_items),
            'rendered_menu_items': [
                menu_item.render_html(self.request, self.context)
                for menu_item in self.menu_items
            ],
        }, request=self.request)

    @cached_property
    def media(self):
        media = Media()
        for item in self.menu_items:
            media += item.media
        return media
