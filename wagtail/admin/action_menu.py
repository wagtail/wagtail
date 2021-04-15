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
    icon_name = ''

    def __init__(self, order=None):
        if order is not None:
            self.order = order

    def get_user_page_permissions_tester(self, context):
        if 'user_page_permissions_tester' in context:
            return context['user_page_permissions_tester']
        return context['user_page_permissions'].for_page(context['page'])

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
            may also contain:
            'user_page_permissions_tester' = a PagePermissionTester for the current user and page
        """
        return (
            context['view'] == 'create'
            or not self.get_user_page_permissions_tester(context).page_locked()
        )

    def get_context(self, request, parent_context):
        """Defines context for the template, overridable to use more data"""
        context = parent_context.copy()
        context.update({
            'label': self.label,
            'url': self.get_url(request, context),
            'name': self.name,
            'classname': self.classname,
            'icon_name': self.icon_name,
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
    icon_name = 'upload'

    def is_shown(self, request, context):
        if context['view'] == 'create':
            return context['user_page_permissions'].for_page(context['parent_page']).can_publish_subpage()
        else:  # view == 'edit' or 'revisions_revert'
            perms_tester = self.get_user_page_permissions_tester(context)
            return (
                not perms_tester.page_locked()
                and perms_tester.can_publish()
            )

    def get_context(self, request, parent_context):
        context = super().get_context(request, parent_context)
        context['is_revision'] = (context['view'] == 'revisions_revert')
        return context


class SubmitForModerationMenuItem(ActionMenuItem):
    label = _("Submit for moderation")
    name = 'action-submit'
    icon_name = 'resubmit'

    def is_shown(self, request, context):
        if not getattr(settings, 'WAGTAIL_MODERATION_ENABLED', True):
            return False

        if context['view'] == 'create':
            return context['parent_page'].has_workflow

        if context['view'] == 'edit':
            perms_tester = self.get_user_page_permissions_tester(context)
            return perms_tester.can_submit_for_moderation() and not perms_tester.page_locked()
        # context == revisions_revert
        return False

    def get_context(self, request, parent_context):
        context = super().get_context(request, parent_context)
        page = context.get('page')
        workflow_state = page.current_workflow_state if page else None
        if workflow_state and workflow_state.status == workflow_state.STATUS_NEEDS_CHANGES:
            context['label'] = _("Resubmit to {}").format(workflow_state.current_task_state.task.name)
        elif page:
            workflow = page.get_workflow()
            if workflow:
                context['label'] = _("Submit to {}").format(workflow.name)
        return context


class WorkflowMenuItem(ActionMenuItem):
    template = 'wagtailadmin/pages/action_menu/workflow_menu_item.html'

    def __init__(self, name, label, launch_modal, *args, **kwargs):
        self.name = name
        self.label = label
        self.launch_modal = launch_modal

        if kwargs.get('icon_name'):
            self.icon_name = kwargs.pop('icon_name')

        super().__init__(*args, **kwargs)

    def get_context(self, request, parent_context):
        context = super().get_context(request, parent_context)
        context['launch_modal'] = self.launch_modal
        context['current_task_state'] = context['page'].current_workflow_task_state
        return context

    def is_shown(self, request, context):
        if context['view'] == 'edit':
            perms_tester = self.get_user_page_permissions_tester(context)
            return not perms_tester.page_locked()


class RestartWorkflowMenuItem(ActionMenuItem):
    label = _("Restart workflow ")
    name = 'action-restart-workflow'
    classname = 'button--icon-flipped'
    icon_name = 'login'

    def is_shown(self, request, context):
        if not getattr(settings, 'WAGTAIL_MODERATION_ENABLED', True):
            return False
        elif context['view'] == 'edit':
            workflow_state = context['page'].current_workflow_state
            perms_tester = self.get_user_page_permissions_tester(context)
            return (
                perms_tester.can_submit_for_moderation()
                and not perms_tester.page_locked()
                and workflow_state
                and workflow_state.user_can_cancel(request.user)
            )
        else:
            return False


class CancelWorkflowMenuItem(ActionMenuItem):
    label = _("Cancel workflow ")
    name = 'action-cancel-workflow'
    icon_name = 'error'

    def is_shown(self, request, context):
        if context['view'] == 'edit':
            workflow_state = context['page'].current_workflow_state
            return workflow_state and workflow_state.user_can_cancel(request.user)
        return False


class UnpublishMenuItem(ActionMenuItem):
    label = _("Unpublish")
    name = 'action-unpublish'
    icon_name = 'download-alt'
    classname = 'action-secondary'

    def is_shown(self, request, context):
        if context['view'] == 'edit':
            perms_tester = self.get_user_page_permissions_tester(context)
            return (
                not perms_tester.page_locked()
                and perms_tester.can_unpublish()
            )

    def get_url(self, request, context):
        return reverse('wagtailadmin_pages:unpublish', args=(context['page'].id,))


class DeleteMenuItem(ActionMenuItem):
    name = 'action-delete'
    label = _("Delete")
    icon_name = 'bin'
    classname = 'action-secondary'

    def is_shown(self, request, context):
        if context['view'] == 'edit':
            perms_tester = self.get_user_page_permissions_tester(context)
            return (
                not perms_tester.page_locked()
                and perms_tester.can_delete()
            )

    def get_url(self, request, context):
        return reverse('wagtailadmin_pages:delete', args=(context['page'].id,))


class LockMenuItem(ActionMenuItem):
    name = 'action-lock'
    label = _("Lock")
    aria_label = _("Apply editor lock")
    icon_name = 'lock'
    classname = 'action-secondary'
    template = 'wagtailadmin/pages/action_menu/lock_unlock_menu_item.html'

    def is_shown(self, request, context):
        return (
            context['view'] == 'edit'
            and not context['page'].locked
            and self.get_user_page_permissions_tester(context).can_lock()
        )

    def get_url(self, request, context):
        return reverse('wagtailadmin_pages:lock', args=(context['page'].id,))

    def render_html(self, request, parent_context):
        context = self.get_context(request, parent_context)
        context['aria_label'] = self.aria_label
        return render_to_string(self.template, context, request=request)


class UnlockMenuItem(LockMenuItem):
    name = 'action-unlock'
    label = _("Unlock")
    aria_label = _("Apply editor lock")
    icon_name = 'lock-open'

    def is_shown(self, request, context):
        return (
            context['view'] == 'edit'
            and context['page'].locked
            and self.get_user_page_permissions_tester(context).can_unlock()
        )

    def get_url(self, request, context):
        return reverse('wagtailadmin_pages:unlock', args=(context['page'].id,))


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
        return (
            'page' in context
            and self.get_user_page_permissions_tester(context).page_locked()
        )

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
            DeleteMenuItem(order=10),
            LockMenuItem(order=15),
            UnlockMenuItem(order=15),
            UnpublishMenuItem(order=20),
            PublishMenuItem(order=30),
            CancelWorkflowMenuItem(order=40),
            RestartWorkflowMenuItem(order=50),
            SubmitForModerationMenuItem(order=60),
            PageLockedMenuItem(order=10000),
        ]
        for hook in hooks.get_hooks('register_page_action_menu_item'):
            action_menu_item = hook()
            if action_menu_item:
                BASE_PAGE_ACTION_MENU_ITEMS.append(action_menu_item)

    return BASE_PAGE_ACTION_MENU_ITEMS


class PageActionMenu:
    template = 'wagtailadmin/pages/action_menu/menu.html'

    def __init__(self, request, **kwargs):
        self.request = request
        self.context = kwargs
        page = self.context.get('page')
        user_page_permissions = UserPagePermissionsProxy(self.request.user)
        self.context['user_page_permissions'] = user_page_permissions
        if page:
            self.context['user_page_permissions_tester'] = user_page_permissions.for_page(page)

        self.menu_items = []

        if page:
            task = page.current_workflow_task
            current_workflow_state = page.current_workflow_state
            is_final_task = current_workflow_state and current_workflow_state.is_at_final_task
            if task:
                actions = task.get_actions(page, request.user)
                workflow_menu_items = []
                for name, label, launch_modal in actions:
                    icon_name = 'edit'
                    if name == "approve":
                        if is_final_task and not getattr(settings, 'WAGTAIL_WORKFLOW_REQUIRE_REAPPROVAL_ON_EDIT', False):
                            label = _("%(label)s and Publish") % {'label': label}
                        icon_name = 'success'

                    item = WorkflowMenuItem(name, label, launch_modal, icon_name=icon_name)

                    if item.is_shown(self.request, self.context):
                        workflow_menu_items.append(item)
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
